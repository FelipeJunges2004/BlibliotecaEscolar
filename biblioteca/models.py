from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone


class AlunoPerfil(models.Model):
    class Serie(models.TextChoices):
        PRIMEIRO = '1EM', '1º ano'
        SEGUNDO = '2EM', '2º ano'
        TERCEIRO = '3EM', '3º ano'

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    matricula = models.CharField(max_length=30, unique=True)
    serie = models.CharField(max_length=3, choices=Serie.choices)

    class Meta:
        verbose_name = 'Perfil de aluno'
        verbose_name_plural = 'Perfis de alunos'
        indexes = [models.Index(fields=['serie'])]

    def __str__(self):
        return f'{self.usuario.username} - {self.matricula}'


class Emprestimo(models.Model):
    aluno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emprestimos')
    nome_livro = models.CharField(max_length=150)
    data_retirada = models.DateField()
    data_devolucao = models.DateField(editable=False)
    devolvido = models.BooleanField(default=False)
    data_devolucao_real = models.DateField(null=True, blank=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devolucoes_confirmadas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_retirada', '-criado_em']
        indexes = [
            models.Index(fields=['devolvido', 'data_devolucao']),
            models.Index(fields=['data_retirada']),
            models.Index(fields=['aluno', 'devolvido']),
            models.Index(fields=['nome_livro']),
        ]

    def save(self, *args, **kwargs):
        self.data_devolucao = self.data_retirada + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def atrasado(self):
        return not self.devolvido and self.data_devolucao < timezone.localdate()

    @property
    def status(self):
        if self.devolvido:
            return 'devolvido'
        if self.atrasado:
            return 'atrasado'
        return 'pendente'

    @property
    def matricula_aluno(self):
        try:
            return self.aluno.perfil.matricula
        except ObjectDoesNotExist:
            return '-'

    @property
    def serie_aluno(self):
        try:
            return self.aluno.perfil.get_serie_display()
        except ObjectDoesNotExist:
            return '-'

    def __str__(self):
        return f'{self.nome_livro} - {self.aluno.username}'


class NotificacaoAtrasoLog(models.Model):
    class Canal(models.TextChoices):
        EMAIL = 'email', 'E-mail'

    class Status(models.TextChoices):
        ENVIADO = 'enviado', 'Enviado'
        ERRO = 'erro', 'Erro'

    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name='notificacoes')
    canal = models.CharField(max_length=20, choices=Canal.choices)
    destino = models.CharField(max_length=150)
    data_referencia = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices)
    mensagem = models.TextField(blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('emprestimo', 'canal', 'data_referencia')
        ordering = ['-enviado_em']
        indexes = [
            models.Index(fields=['data_referencia', 'canal']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.emprestimo_id} - {self.canal} - {self.status}'
