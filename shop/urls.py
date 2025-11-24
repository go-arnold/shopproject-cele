from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.homeVue, name='home'),
    path('category/<int:pk>/', views.categoryVue, name='category_detail'),
    path('products/', views.allProducts, name='all_products'),
    path('product/<int:pk>/', views.productVue, name='product_detail'),
    path('product/<int:pk>/testimony/add/',
         views.add_testimony, name='add_testimony'),
    path("results/", views.results, name="results"),
    path('favori/<int:product_id>/ajouter/',
         views.add_favorite, name='add_favorite'),
    path('favori/<int:product_id>/supprimer/',
         views.remove_favorite, name='remove_favorite'),
    path('favori/<int:product_id>/toggle/',
         views.toggle_favorite, name='toggle_favorite'),
    path("favoris/", views.favorites_list, name="favorites_list"),
    path('about/', views.aboutUs, name='about_us'),
    path('cart/', views.cart, name='cart'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
