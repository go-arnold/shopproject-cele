from django.urls import path

from django.conf.urls.static import static
from django.conf import settings
from shop.view_components.general import home, cart, celebobo, testimony
from shop.view_components.produits import (
    category,
    favorite,
    liste_products,
    search_results,
    single_product,
)
from shop.view_components.echanges import (
    debut,
    details,
    json_conversations,
    liste,
    notifications,
)


urlpatterns = [
    path("", home.homeVue, name="home"),
    path("category/<int:pk>/", category.categoryVue, name="category_detail"),
    path("products/", liste_products.allProducts, name="all_products"),
    path("product/<int:pk>/", single_product.productVue, name="product_detail"),
    path(
        "product/<int:pk>/testimony/add/", testimony.add_testimony, name="add_testimony"
    ),
    path("results/", search_results.results, name="results"),
    path(
        "favori/<int:product_id>/ajouter/", favorite.add_favorite, name="add_favorite"
    ),
    path(
        "favori/<int:product_id>/supprimer/",
        favorite.remove_favorite,
        name="remove_favorite",
    ),
    path(
        "favori/<int:product_id>/toggle/",
        favorite.toggle_favorite,
        name="toggle_favorite",
    ),
    path("favoris/", favorite.favorites_list, name="favorites_list"),
    path("about/", celebobo.aboutUs, name="about_us"),
    path("add-to-cart/", cart.add_to_cart, name="add_to_cart"),
    path("update-cart/", cart.update_cart, name="update_cart"),
    path("remove-from-cart/", cart.remove_from_cart, name="remove_from_cart"),
    path("cart/", cart.cart_view, name="cart"),
    path("assistant/", celebobo.assistant, name="assistant"),
    path("messages/", liste.messages, name="messages"),
    path(
        "start-conversation/",
        debut.start_conversation_from_cart,
        name="start_conversation_from_cart",
    ),
    path(
        "conversation/<int:conversation_id>/",
        details.conversation_detail,
        name="conversation_detail",
    ),
    path(
        "conversation/<int:conversation_id>/json/",
        json_conversations.conversation_messages_json,
        name="conversation_messages_json",
    ),
    path(
        "conversation/<int:conversation_id>/send/",
        json_conversations.send_message_ajax,
        name="send_message_ajax",
    ),
    path(
        "conversation/<int:conversation_id>/fetch/",
        json_conversations.fetch_new_messages_ajax,
        name="fetch_new_messages_ajax",
    ),
    path("notifications/", notifications.notifications_view, name="notifications"),
    path(
        "notifications/<int:notification_id>/assign/",
        notifications.assign_revendeur,
        name="assign_revendeur",
    ),
    path(
        "notifications/<int:notification_id>/assign_discuss/",
        notifications.assign_revendeur_discussion,
        name="assign_revendeur_discuss",
    ),
    path(
        "notifications/<int:notification_id>/mukubwa-reply/",
        notifications.mukubwa_reply,
        name="mukubwa_reply",
    ),
    path(
        "notifications/<int:notification_id>/revendeur-reply/",
        notifications.revendeur_reply,
        name="revendeur_reply",
    ),
    path("conversations/", liste.list_conversations, name="list_conversations"),
    path("conversations/new/", debut.conversation_new, name="conversation_new"),
    path("discussions/", liste.disc, name="discussions"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
