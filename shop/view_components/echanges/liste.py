from django.utils import timezone
from django.shortcuts import render
from shop.models import Conversation, Message
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def list_conversations(request):
    """
    Liste simple des conversations de l'utilisateur.
    Recherche server-side sur:
      - contenu du dernier message
      - nom des autres participants
      - id de la commande (related_order.id) si présent
    Aucun JS : tout via paramètre GET 'q'.
    """
    q = request.GET.get("q", "").strip()

    qs = Conversation.objects.filter(participants=request.user).order_by("-created_at")

    paginator = Paginator(qs, 8)
    page = request.GET.get("page")
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    conversations_info = []
    for conv in page_obj.object_list:
        last_msg = (
            Message.objects.filter(conversation=conv).order_by("-timestamp").first()
        )
        last_content = last_msg.content if last_msg else ""
        last_sender = last_msg.sender if last_msg else None
        last_timestamp = last_msg.timestamp if last_msg else None

        others = conv.participants.exclude(id=request.user.id)
        other = others.first() if others.exists() else None

        conversations_info.append(
            {
                "conversation": conv,
                "other": other,
                "last_content": last_content,
                "last_sender": last_sender,
                "last_timestamp": last_timestamp,
            }
        )
    if q:
        q_lower = q.lower()
        filtered = []
        for item in conversations_info:
            matches = False

            if item["last_content"] and q_lower in item["last_content"].lower():
                matches = True

            other = item["other"]
            if other:
                fullname = (other.get_full_name() or other.username).lower()
                if q_lower in fullname or q_lower in other.username.lower():
                    matches = True

            conv = item["conversation"]
            if q.isdigit() and conv.related_order and str(conv.related_order.id) == q:
                matches = True

            if matches:
                filtered.append(item)

        conversations_info = filtered

    context = {
        "conversations_info": conversations_info,
        "query": q,
        "now": timezone.now(),
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "total_count": paginator.count,
    }
    return render(request, "shop/list_discussions.html", context)


def messages(request):
    html_to_render2 = "shop/login_required.html"

    if not request.user.is_authenticated:
        return render(request, html_to_render2)
    return render(request, "shop/conversations.html")


def disc(request):
    return render(request, "shop/list_discussions.html")
