from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import AlunoPerfil, Emprestimo


class CadastroAlunoForm(UserCreationForm):
    nome_completo = forms.CharField(max_length=150, label='Nome completo')
    email = forms.EmailField(label='E-mail')
    matricula = forms.CharField(max_length=30, label='Numero de matricula')
    serie = forms.ChoiceField(choices=AlunoPerfil.Serie.choices, label='Serie')

    class Meta:
        model = User
        fields = ('nome_completo', 'email', 'username', 'matricula', 'serie', 'password1', 'password2')
        labels = {'username': 'Nome de usuario'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome_completo'].widget.attrs.update({'placeholder': 'Ex.: Maria Silva'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Ex.: aluno@escola.com'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Ex.: maria.silva'})
        self.fields['matricula'].widget.attrs.update({'placeholder': 'Ex.: 202600123'})

    def clean_matricula(self):
        matricula = self.cleaned_data['matricula'].strip()
        if AlunoPerfil.objects.filter(matricula=matricula).exists():
            raise forms.ValidationError('Este numero de matricula ja esta em uso.')
        return matricula

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail ja esta em uso.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nome_completo']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            AlunoPerfil.objects.create(
                usuario=user,
                matricula=self.cleaned_data['matricula'],
                serie=self.cleaned_data['serie'],
            )
        return user


class LoginAlunoForm(AuthenticationForm):
    username = forms.CharField(label='Nome de usuario')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Seu usuario'})


class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = ('nome_livro', 'data_retirada')
        widgets = {
            'nome_livro': forms.TextInput(attrs={'placeholder': 'Digite o nome do livro'}),
            'data_retirada': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'nome_livro': 'Nome do livro',
            'data_retirada': 'Data de retirada',
        }


class FiltroEmprestimoAdminForm(forms.Form):
    STATUS_CHOICES = (
        ('todos', 'Todos os status'),
        ('pendente', 'Pendentes'),
        ('devolvido', 'Devolvidos'),
        ('atrasado', 'Atrasados'),
    )

    ORDENACAO_CHOICES = (
        ('-data_retirada', 'Retirada (mais recente)'),
        ('data_retirada', 'Retirada (mais antiga)'),
        ('data_devolucao', 'Devolucao (mais proxima)'),
        ('-data_devolucao', 'Devolucao (mais distante)'),
        ('aluno__first_name', 'Aluno (A-Z)'),
        ('-aluno__first_name', 'Aluno (Z-A)'),
        ('nome_livro', 'Livro (A-Z)'),
        ('-nome_livro', 'Livro (Z-A)'),
    )

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, initial='todos')
    aluno = forms.CharField(required=False, label='Aluno', max_length=150)
    matricula = forms.CharField(required=False, label='Matricula', max_length=30)
    serie = forms.ChoiceField(choices=[('', 'Todas as series')] + list(AlunoPerfil.Serie.choices), required=False, label='Serie')
    livro = forms.CharField(required=False, label='Livro', max_length=150)
    ordenacao = forms.ChoiceField(choices=ORDENACAO_CHOICES, required=False, initial='-data_retirada')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aluno'].widget.attrs.update({'placeholder': 'Buscar por nome do aluno'})
        self.fields['matricula'].widget.attrs.update({'placeholder': 'Buscar por numero de matricula'})
        self.fields['livro'].widget.attrs.update({'placeholder': 'Buscar por nome do livro'})
