
from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('produits/', views.admin_products, name='admin_products'),
    path('produits/ajouter/', views.add_product, name='add_product'),
    path('produits/<int:product_id>/modifier/',
         views.edit_product, name='edit_product'),
    path('produits/<int:product_id>/supprimer/',
         views.delete_product, name='delete_product'),
    path('produits/<int:product_id>/', views.view_product, name='view_product'),
    path('ventes/', views.liste_ventes, name='liste_ventes'),
    path('ventes_rev/', views.liste_ventes_rev, name='liste_ventes_rev'),


    path('ventes/ajouter/', views.ajouter_vente, name='ajouter_vente'),
    path('ventes/<int:vente_id>/modifier/',
         views.modifier_vente, name='modifier_vente'),
    path('ventes/<int:vente_id>/supprimer/',
         views.supprimer_vente, name='supprimer_vente'),
    path('produit/<int:product_id>/details/',
         views.get_product_details, name='get_product_details'),
    path('ventes/export/excel/', views.export_ventes_excel,
         name='export_ventes_excel'),
    path('ventes/export/pdf/', views.export_ventes_pdf, name='export_ventes_pdf'),
    path("graphs/", views.dashboard_ventes, name="dashboard_ventes"),
    path("dashboard/pdf/", views.dashboard_pdf, name="dashboard_pdf"),




]
