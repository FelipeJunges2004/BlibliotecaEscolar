import io
from collections import OrderedDict
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CadastroAlunoForm, EmprestimoForm, FiltroEmprestimoAdminForm, LoginAlunoForm
from .models import AlunoPerfil, Emprestimo


class LoginAlunoView(LoginView):
    template_name = 'biblioteca/login.html'
    authentication_form = LoginAlunoForm


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CadastroAlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save()
            login(request, aluno)
            return redirect('dashboard')
    else:
        form = CadastroAlunoForm()

    return render(request, 'biblioteca/cadastro.html', {'form': form})


@login_required
def dashboard(request):
    emprestimos = Emprestimo.objects.filter(aluno=request.user)

    if request.method == 'POST':
        form = EmprestimoForm(request.POST)
        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.aluno = request.user
            emprestimo.save()
            messages.success(request, 'Retirada registrada com sucesso.')
            return redirect('dashboard')
    else:
        form = EmprestimoForm()

    hoje = timezone.localdate()
    total_pendentes = emprestimos.filter(devolvido=False, data_devolucao__gte=hoje).count()
    total_atrasados = emprestimos.filter(devolvido=False, data_devolucao__lt=hoje).count()
    total_devolvidos = emprestimos.filter(devolvido=True).count()

    return render(
        request,
        'biblioteca/dashboard.html',
        {
            'form': form,
            'emprestimos': emprestimos,
            'total_retiradas': emprestimos.count(),
            'total_pendentes': total_pendentes,
            'total_atrasados': total_atrasados,
            'total_devolvidos': total_devolvidos,
        },
    )


def aplicar_filtros_admin(queryset, form, hoje):
    if not form.is_valid():
        return queryset.order_by('-data_retirada')

    status = form.cleaned_data.get('status') or 'todos'
    aluno = (form.cleaned_data.get('aluno') or '').strip()
    matricula = (form.cleaned_data.get('matricula') or '').strip()
    serie = (form.cleaned_data.get('serie') or '').strip()
    livro = (form.cleaned_data.get('livro') or '').strip()
    ordenacao = form.cleaned_data.get('ordenacao') or '-data_retirada'

    if status == 'pendente':
        queryset = queryset.filter(devolvido=False, data_devolucao__gte=hoje)
    elif status == 'devolvido':
        queryset = queryset.filter(devolvido=True)
    elif status == 'atrasado':
        queryset = queryset.filter(devolvido=False, data_devolucao__lt=hoje)

    if aluno:
        queryset = queryset.filter(
            Q(aluno__first_name__icontains=aluno)
            | Q(aluno__last_name__icontains=aluno)
            | Q(aluno__username__icontains=aluno)
        )

    if matricula:
        queryset = queryset.filter(aluno__perfil__matricula__icontains=matricula)

    if serie:
        queryset = queryset.filter(aluno__perfil__serie=serie)

    if livro:
        queryset = queryset.filter(nome_livro__icontains=livro)

    return queryset.order_by(ordenacao, '-id')


def montar_graficos_admin(hoje):
    inicio_periodo = hoje.replace(day=1)
    for _ in range(5):
        inicio_periodo = (inicio_periodo.replace(day=1) - timedelta(days=1)).replace(day=1)

    qs_mes = (
        Emprestimo.objects.filter(data_retirada__gte=inicio_periodo)
        .annotate(mes=TruncMonth('data_retirada'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    mapa = OrderedDict()
    cursor = inicio_periodo
    while cursor <= hoje.replace(day=1):
        mapa[cursor.strftime('%m/%Y')] = 0
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
    for item in qs_mes:
        mapa[item['mes'].strftime('%m/%Y')] = item['total']

    max_mes = max(mapa.values()) if mapa else 1
    grafico_retiradas_mes = [
        {'label': label, 'total': total, 'percentual': int((total / max_mes) * 100) if max_mes else 0}
        for label, total in mapa.items()
    ]

    atraso_por_serie_qs = (
        Emprestimo.objects.filter(devolvido=False, data_devolucao__lt=hoje)
        .values('aluno__perfil__serie')
        .annotate(total=Count('id'))
    )
    atraso_map = {item['aluno__perfil__serie']: item['total'] for item in atraso_por_serie_qs}
    raw_series = [{'label': label, 'total': atraso_map.get(code, 0)} for code, label in AlunoPerfil.Serie.choices]
    max_serie = max([item['total'] for item in raw_series] + [1])
    grafico_atraso_serie = [
        {**item, 'percentual': int((item['total'] / max_serie) * 100) if max_serie else 0}
        for item in raw_series
    ]

    top_livros_qs = (
        Emprestimo.objects.values('nome_livro').annotate(total=Count('id')).order_by('-total', 'nome_livro')[:5]
    )
    raw_livros = [{'label': item['nome_livro'], 'total': item['total']} for item in top_livros_qs]
    max_livro = max([item['total'] for item in raw_livros] + [1])
    grafico_top_livros = [
        {**item, 'percentual': int((item['total'] / max_livro) * 100) if max_livro else 0}
        for item in raw_livros
    ]

    return grafico_retiradas_mes, grafico_atraso_serie, grafico_top_livros


def exportar_pdf_emprestimos(filtrados):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception as exc:
        return HttpResponse(
            f'Recurso de PDF indisponivel. Instale reportlab. Erro: {exc}',
            status=500,
            content_type='text/plain; charset=utf-8',
        )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, altura = A4

    y = altura - 40
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(40, y, 'Relatorio de retiradas - Biblioteca Escolar')
    y -= 24
    pdf.setFont('Helvetica', 9)
    pdf.drawString(40, y, f'Gerado em: {timezone.localtime().strftime("%d/%m/%Y %H:%M")}')
    y -= 20

    headers = ['Aluno', 'Matricula', 'Serie', 'Livro', 'Retirada', 'Limite', 'Status']
    col_x = [40, 130, 200, 250, 400, 455, 515]

    pdf.setFont('Helvetica-Bold', 8)
    for i, header in enumerate(headers):
        pdf.drawString(col_x[i], y, header)
    y -= 14
    pdf.setFont('Helvetica', 7)

    for item in filtrados.iterator():
        if y < 40:
            pdf.showPage()
            y = altura - 40
            pdf.setFont('Helvetica-Bold', 8)
            for i, header in enumerate(headers):
                pdf.drawString(col_x[i], y, header)
            y -= 14
            pdf.setFont('Helvetica', 7)

        row = [
            (item.aluno.first_name or '-')[:18],
            item.matricula_aluno[:12],
            item.serie_aluno[:8],
            item.nome_livro[:28],
            item.data_retirada.strftime('%d/%m/%Y'),
            item.data_devolucao.strftime('%d/%m/%Y'),
            item.status.title(),
        ]
        for i, text in enumerate(row):
            pdf.drawString(col_x[i], y, text)
        y -= 12

    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="emprestimos_filtrados.pdf"'
    return response


@staff_member_required
def painel_admin(request):
    hoje = timezone.localdate()
    base_qs = Emprestimo.objects.select_related('aluno', 'aluno__perfil', 'confirmado_por')
    form = FiltroEmprestimoAdminForm(request.GET or None)
    filtrados = aplicar_filtros_admin(base_qs, form, hoje)

    if request.GET.get('export') == 'pdf':
        return exportar_pdf_emprestimos(filtrados)

    paginator = Paginator(filtrados, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_params = request.GET.copy()
    query_params.pop('page', None)

    resumo = Emprestimo.objects.aggregate(
        total_pendentes=Count('id', filter=Q(devolvido=False, data_devolucao__gte=hoje)),
        total_atrasados=Count('id', filter=Q(devolvido=False, data_devolucao__lt=hoje)),
        total_devolvidos=Count('id', filter=Q(devolvido=True)),
    )
    grafico_retiradas_mes, grafico_atraso_serie, grafico_top_livros = montar_graficos_admin(hoje)

    context = {
        'form': form,
        'page_obj': page_obj,
        'query_string': query_params.urlencode(),
        'total_alunos': User.objects.filter(is_staff=False).count(),
        'total_pendentes': resumo['total_pendentes'],
        'total_atrasados': resumo['total_atrasados'],
        'total_devolvidos': resumo['total_devolvidos'],
        'grafico_retiradas_mes': grafico_retiradas_mes,
        'grafico_atraso_serie': grafico_atraso_serie,
        'grafico_top_livros': grafico_top_livros,
    }
    return render(request, 'biblioteca/painel_admin.html', context)


@staff_member_required
def marcar_devolvido(request, emprestimo_id):
    if request.method != 'POST':
        messages.error(request, 'Metodo nao permitido.')
        return redirect('painel_admin')

    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id)
    if not emprestimo.devolvido:
        emprestimo.devolvido = True
        emprestimo.data_devolucao_real = timezone.localdate()
        emprestimo.confirmado_por = request.user
        emprestimo.save(update_fields=['devolvido', 'data_devolucao_real', 'confirmado_por'])
        messages.success(request, f'Livro "{emprestimo.nome_livro}" marcado como devolvido.')
    else:
        messages.info(request, f'Livro "{emprestimo.nome_livro}" ja estava devolvido.')

    next_url = request.POST.get('next') or reverse('painel_admin')
    return redirect(next_url)
