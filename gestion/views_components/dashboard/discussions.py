from django.shortcuts import render
from django.contrib.auth.models import Group
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from shop.models import (
    Conversation,
)
from utils.decorators import admin_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


@admin_required
def conclure_discussion(request, conversation_id):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if (user not in rev) and (user not in muk):
        raise PermissionDenied()
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.method == "POST":
        conversation.related_order.status = "terminé"
        conversation.related_order.save()
        messages.success(
            request,
            "Le status de l'ordre associé à cette conversation a été mise à jour avec succès.",
        )
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect("list_conversations")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(
            request,
            "gestion/conclure_discussion_partial.html",
            {"conversation": conversation},
        )
    return render(
        request, "gestion/conclure_discussion.html", {"conversation": conversation}
    )
