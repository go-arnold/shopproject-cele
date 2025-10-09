
from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('produits/', views.admin_products, name='admin_products'),
    path('produits/ajouter/', views.add_product, name='add_product'),
    path('produits/<int:product_id>/modifier/', views.edit_product, name='edit_product'),
    path('produits/<int:product_id>/supprimer/', views.delete_product, name='delete_product'),
    path('produits/<int:product_id>/', views.view_product, name='view_product'),
]
