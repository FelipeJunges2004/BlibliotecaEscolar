from django.contrib import admin

from .models import AlunoPerfil, Emprestimo, NotificacaoAtrasoLog


@admin.register(AlunoPerfil)
class AlunoPerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'matricula', 'serie')
    search_fields = ('usuario__username', 'usuario__first_name', 'matricula')
    list_filter = ('serie',)


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = (
        'nome_livro',
        'aluno',
        'data_retirada',
        'data_devolucao',
        'devolvido',
        'data_devolucao_real',
        'confirmado_por',
    )
    search_fields = ('nome_livro', 'aluno__username', 'aluno__first_name', 'aluno__perfil__matricula')
    list_filter = ('data_retirada', 'data_devolucao', 'devolvido', 'aluno__perfil__serie')


@admin.register(NotificacaoAtrasoLog)
class NotificacaoAtrasoLogAdmin(admin.ModelAdmin):
    list_display = ('emprestimo', 'canal', 'destino', 'status', 'data_referencia', 'enviado_em')
    search_fields = ('destino', 'emprestimo__nome_livro', 'emprestimo__aluno__username')
    list_filter = ('canal', 'status', 'data_referencia')
