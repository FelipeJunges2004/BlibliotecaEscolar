from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import LoginAlunoView, cadastro, dashboard, marcar_devolvido, painel_admin

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', LoginAlunoView.as_view(), name='login'),
    path('cadastro/', cadastro, name='cadastro'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('painel-admin/', painel_admin, name='painel_admin'),
    path('painel-admin/emprestimo/<int:emprestimo_id>/devolver/', marcar_devolvido, name='marcar_devolvido'),
]
