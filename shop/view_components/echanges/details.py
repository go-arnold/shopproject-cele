from django.shortcuts import render, get_object_or_404
from shop.models import Conversation, Message
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        conversation.participants.add(request.user)

    messages = Message.objects.filter(conversation=conversation).order_by("timestamp")

    return render(
        request,
        "shop/discussions.html",
        {
            "conversation": conversation,
            "messages": messages,
            "conversation_name": conversation.display_name,
            "id_id": conversation.id,
        },
    )
