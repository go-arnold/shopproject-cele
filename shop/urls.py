from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from . import views_cart
from .views import cart_view, list_conversations
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
    # path('cart/', views.cart, name='cart'),
    path("add-to-cart/", views_cart.add_to_cart, name="add_to_cart"),
    path("update-cart/", views_cart.update_cart, name="update_cart"),
    path("remove-from-cart/", views_cart.remove_from_cart, name="remove_from_cart"),
    path("cart/", cart_view, name="cart"),
    path("assistant/", views.assistant, name="assistant"),
    path("profile/", views.profile, name="profile"),
    path("messages/", views.messages, name="messages"),
    path("start-conversation/", views.start_conversation_from_cart,
         name="start_conversation_from_cart"),
    path("conversation/<int:conversation_id>/",
         views.conversation_detail, name="conversation_detail"),
    path("conversation/<int:conversation_id>/json/",
         views.conversation_messages_json, name="conversation_messages_json"),
    path("conversation/<int:conversation_id>/send/",
         views.send_message_ajax, name="send_message_ajax"),
    path("conversation/<int:conversation_id>/fetch/",
         views.fetch_new_messages_ajax, name="fetch_new_messages_ajax"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:notification_id>/assign/",
         views.assign_revendeur, name="assign_revendeur"),
    path("notifications/<int:notification_id>/mukubwa-reply/",
         views.mukubwa_reply, name="mukubwa_reply"),
    path("notifications/<int:notification_id>/revendeur-reply/",
         views.revendeur_reply, name="revendeur_reply"),
    path("conversations/", views.list_conversations, name="list_conversations"),
    path("conversations/new/", views.conversation_new, name="conversation_new"),

    path("discussions/", views.disc, name="discussions"),




]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
