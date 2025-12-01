from shop.models import Notification, Message, Conversation


def notifications(request):
    if not request.user.is_authenticated:
        return {
            "notifications": [],
            "notif_count": 0,
            "notify_message": False
        }

    # Notifications
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    notif_count = notifications.count()

    # Conversations de l'utilisateur
    conversations = (
        Conversation.objects.filter(participants=request.user)
        .prefetch_related("messages")
        .order_by("-created_at")
    )

    notify_me = False
    msg_count = 0
    for conv in conversations:
        last_msg = conv.messages.order_by("-timestamp").first()

        if not last_msg:
            continue

        if last_msg.sender != request.user:
            notify_me = True
            msg_count += 1
            break
    if msg_count > 0:
        notif_signal = True
    else:
        notif_signal = False
    return {
        "notifications": notifications,
        "notif_count": notif_count,
        "notify_message": notify_me,
        "msg_count": msg_count,
        "notif_signal": notif_signal,
    }
