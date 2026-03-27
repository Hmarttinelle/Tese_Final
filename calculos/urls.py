# calculos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL para a página inicial
    path('', views.index_view, name='pagina_inicial'),

    # URL para a página de vigas
    path('viga/', views.viga_view, name='viga_dimensionamento'),
    
    # URL para a página de pilares
    path('pilar/', views.pilar_view, name='pilar_dimensionamento'),

    # URL para a página de sapatas
    path('sapata/', views.sapata_view, name='sapata_dimensionamento'),
    
    # URL para a página de historico
    path('historico/', views.historico_view, name='historico_calculos'),

    # URL para a página de historico detalhe
    path('historico/<int:calculo_id>/', views.historico_detalhe_view, name='historico_detalhe'),

    # URL para deletar historico
    path('historico/delete/<int:calculo_id>/', views.historico_delete_view, name='historico_delete'),

    # URL de configuração
    path('configuracao/', views.configuracao_view, name='configuracao_sistema'),

    # NOVA URL PARA GERAR O RELATÓRIO PDF
    path('relatorio/<int:calculo_id>/pdf/', views.gerar_relatorio_pdf_view, name='gerar_relatorio_pdf'),
]