from django.urls import path
from . import views

urlpatterns = [
    path('alterar_dados/', views.alterar_dados, name='alterar_dados'),
    path('cadastro_garantia/', views.cadastro_garantia, name='cadastro_garantia'),
    path('consultar_garantia/', views.consultar_garantia, name='consultar_garantia'),
    path('cadastro_habito/', views.cadastro_habito, name='cadastro_habito'),
    path('progressos/', views.progressos, name='progressos'),
    path('atividade_diaria/', views.atividade_diaria, name='atividade_diaria'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('editar_habito/<int:habito_id>/', views.editar_habito, name='editar_habito'),
    path('api/cliente/update/', views.update_cliente, name='update_cliente'),
    path('api/registrar_atividade/', views.registrar_atividade, name='registrar_atividade'),
    path('api/dados_relatorio/', views.api_dados_relatorio, name='api_dados_relatorio'),
]