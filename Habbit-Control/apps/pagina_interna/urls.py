from django.urls import path
from . import meta_views, views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('alterar_dados/', views.alterar_dados, name='alterar_dados'),
    path('cadastro_garantia/', views.cadastro_garantia, name='cadastro_garantia'),
    path('consultar_garantia/', views.consultar_garantia, name='consultar_garantia'),
    path('cadastro_habito/', views.cadastro_habito, name='cadastro_habito'),
    path('progressos/', views.progressos, name='progressos'),
    path('atividade_diaria/', views.atividade_diaria, name='atividade_diaria'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('metas/', meta_views.metas, name='metas'),
    path('metas/<int:meta_id>/excluir/', meta_views.excluir_meta, name='excluir_meta'),
    path('metas/<int:meta_id>/compartilhar/', meta_views.ativar_compartilhamento_meta, name='ativar_compartilhamento_meta'),
    path('metas/<int:meta_id>/desativar-compartilhamento/', meta_views.desativar_compartilhamento_meta, name='desativar_compartilhamento_meta'),
    path('metas/assistente/sugerir/', meta_views.assistente_sugerir_meta, name='assistente_sugerir_meta'),
    path('meta/publica/<str:token>/', meta_views.meta_publica, name='meta_publica'),
    path('parceiro/metas/', meta_views.metas_partilhadas, name='metas_partilhadas'),
    path('editar_habito/<int:habito_id>/', views.editar_habito, name='editar_habito'),
    path('api/cliente/update/', views.update_cliente, name='update_cliente'),
    path('api/registrar_atividade/', views.registrar_atividade, name='registrar_atividade'),
    path('api/dados_relatorio/', views.api_dados_relatorio, name='api_dados_relatorio'),
]
