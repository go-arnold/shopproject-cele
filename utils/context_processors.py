from shop.models import Notification, Conversation
from django.db.models import Max

# from shop.cart import Cart
from shop.view_components.general.cart import Cart


def cart_counter(request):
    cart = Cart(request)
    return {"cart_count": len(cart)}


def notifications(request):
    if not request.user.is_authenticated:
        return {
            "notifications": [],
            "notif_count": 0,
            "notify_message": False,
            "msg_count": 0,
            "notif_signal": False,
        }

    notifications_qs = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    notif_count = notifications_qs.count()
    not_read_notif = (
        Notification.objects.filter(user=request.user)
        .filter(is_read=False)
        .order_by("-created_at")
        .count()
    )

    conversations_with_last_message = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_msg_id=Max("messages__id"), last_msg_sender=Max("messages__sender_id")
    )

    msg_count = conversations_with_last_message.filter(
        last_msg_sender=request.user.id
    ).count()
    notify_message = msg_count > 0
    notif_signal = notify_message

    return {
        "notifications": notifications_qs,
        "notif_count": notif_count,
        "notify_message": notify_message,
        "msg_count": msg_count,
        "notif_signal": notif_signal,
        "not_read_notif": not_read_notif,
    }
