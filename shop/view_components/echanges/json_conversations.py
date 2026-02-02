from django.templatetags.static import static
from utils.email_custom import send_html_email
from django.shortcuts import get_object_or_404
from shop.models import Conversation, Message, Notification
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def conversation_messages_json(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        return JsonResponse({"error": "Access denied"}, status=403)

    messages = Message.objects.filter(conversation=conversation).order_by("timestamp")

    data = []
    for m in messages:
        data.append(
            {
                "id": m.id,
                "sender_id": m.sender.id,
                "sender_name": m.sender.username,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "is_me": (m.sender == request.user),
            }
        )

    return JsonResponse({"messages": data})


@login_required
def send_message_ajax(request, conversation_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        return JsonResponse({"error": "Access denied"}, status=403)

    content = request.POST.get("content", "").strip()
    image = request.FILES.get("image")

    if not content and not image:
        return JsonResponse({"error": "Message vide"}, status=400)

    msg = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content if content else None,
        image=image if image else None,
    )
    if not conversation.is_from_cart:
        is_first = Message.objects.filter(conversation=conversation).count() == 1

        if is_first:
            try:
                mukubwa_group = Group.objects.get(name="mukubwa")
                mukubwa_users = mukubwa_group.user_set.all()
            except Group.DoesNotExist:
                mukubwa_users = []
            recipients = []
            for admin in mukubwa_users:
                if admin.email:
                    recipients.append(admin.email)
                Notification.objects.create(
                    user=admin,
                    title=f"Nouvelle discussion par {request.user}",
                    body=f"{request.user} a démarré une nouvelle discussion.",
                    conversation=conversation,
                    type="chat",
                )
            subject = f"[ CELEBOBO-BUSINESS ] Nouvelle Discussion demandée par un {request.user}"
            template_name = "shop/email_notify_mukubwa.html"
            text_content = f"{request.user} a envoyé une demande d'achat.\n\n\n {msg.content} \n\n Notification générée automatiquement par votre système"
            context = {
                "logo_url": request.build_absolute_uri(
                    static("static-img/logo-white.png")
                ),
                "msg": msg,
                "yes": True,
            }
            if isinstance(recipients, str):
                recipients = [recipients]
            try:
                send_html_email(
                    subject, recipients, template_name, text_content, context
                )
                print("Email envoyé avec succès à:", recipients)
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'email : {e}")

    return JsonResponse(
        {
            "id": msg.id,
            "sender_id": msg.sender.id,
            "content": msg.content,
            "image_url": msg.image.url if msg.image else None,
            "timestamp": msg.timestamp.isoformat(),
            "is_me": True,
        }
    )


@login_required
def fetch_new_messages_ajax(request, conversation_id):
    last_id = int(request.GET.get("last_id", 0))

    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        return JsonResponse({"error": "Access denied"}, status=403)

    new_messages = Message.objects.filter(
        conversation=conversation, id__gt=last_id
    ).order_by("timestamp")

    data = []
    for m in new_messages:
        data.append(
            {
                "id": m.id,
                "sender_id": m.sender.id,
                "sender_name": m.sender.username,
                "content": m.content,
                "image_url": m.image.url if m.image else None,
                "timestamp": m.timestamp.isoformat(),
                "is_me": (m.sender == request.user),
            }
        )

    return JsonResponse({"messages": data})
