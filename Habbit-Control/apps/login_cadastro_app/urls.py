from django.urls import path
from . import partner_views, views

urlpatterns = [
    path('', views.index, name='index'), 
    path('cadastro/cliente/', views.cadastro_cliente, name='cadastro_cliente'),
    path('login/', views.login, name='login'),
    path('parceiro/cadastro/', partner_views.cadastro_parceiro, name='cadastro_parceiro'),
    path('parceiro/login/', partner_views.login_parceiro, name='login_parceiro'),
    path('consentimento/', views.consentimento, name='consentimento'),
    path('logout/', views.logout_view, name='logout'),
]