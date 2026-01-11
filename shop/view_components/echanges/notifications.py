from utils.email_custom import send_html_email
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from shop.models import Notification
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


@login_required
def notifications_view(request):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user not in rev and user not in muk:
        raise PermissionDenied()
    else:
        notifications = Notification.objects.filter(user=user).order_by("-created_at")
        # notif_count = int(notifications.count())

        try:
            revendeur_group = Group.objects.get(name="revendeur")
            revendeurs = revendeur_group.user_set.all()
            mukubwa_group = Group.objects.get(name="mukubwa")
            mukubwas = mukubwa_group.user_set.all()

            s_users = User.objects.filter(is_superuser=True)
        except Group.DoesNotExist:
            revendeurs = []
            mukubwas = []
        paginator = Paginator(notifications, 10)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return render(
            request,
            "shop/mukubwa_revendeur.html",
            {
                "notifications": page_obj.object_list,
                "revendeurs": revendeurs,
                "mukubwas": mukubwas,
                "s_users": s_users,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "start_index": page_obj.start_index(),
                "end_index": page_obj.end_index(),
                "total_count": paginator.count,
            },
        )


@login_required
def assign_revendeur(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="mukubwa").exists():
        raise PermissionDenied()

    revendeur_id = request.POST.get("revendeur_id")

    if not revendeur_id:
        messages.error(request, "Veuillez sélectionner un revendeur.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    revendeur = get_object_or_404(User, id=revendeur_id)
    try:
        conve = notification.conversation
        order = conve.related_order
        order.assigned_revendeur = revendeur
        order.save()
    except Exception as e:
        print(e)
    conversation = notification.conversation
    conversation.participants.add(revendeur)

    Notification.objects.filter(
        conversation=conversation, user__groups__name="mukubwa", type="order"
    ).update(is_order_assigned=True)

    Notification.objects.create(
        user=revendeur,
        conversation=conversation,
        type="order",
        title="Assignation de commande",
        body=f"Vous avez été assigné à la commande #{conversation.related_order.id}",
    )
    subject = "[CELEBOBO-BUSINESS] NOUVELLE ASSIGNATION- UNE COMMANDE"
    text_content = f"Vous avez été assigné à la commande #{conversation.related_order.id}\n\n La conversation sera du type Commande, Agissez vite s'il vous plait !"
    if revendeur.email:
        send_html_email(
            subject,
            [revendeur.email],
            "shop/assign_rev_email.html",
            text_content,
            {
                "conversation": conversation,
            },
        )

    return redirect("notifications")


@login_required
def assign_revendeur_discussion(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="mukubwa").exists():
        raise PermissionDenied()

    revendeur_id = request.POST.get("revendeur_id")

    if not revendeur_id:
        messages.error(request, "Veuillez sélectionner un revendeur.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    revendeur = get_object_or_404(User, id=revendeur_id)

    conversation = notification.conversation
    conversation.participants.add(revendeur)

    Notification.objects.filter(
        conversation=conversation, user__groups__name="mukubwa", type="chat"
    ).update(is_order_assigned=True)

    Notification.objects.create(
        user=revendeur,
        conversation=conversation,
        type="order",
        title="Assignation de discussion",
        body="Vous avez été appelé à avoir une nouvelle discussion avec un client.\n\n La conversation sera du type Discussion-Chat, Agissez vite s'il vous plait pour la satisafaction du client!",
    )
    subject = "[CELEBOBO-BUSINESS] NOUVELLE ASSIGNATION - SIMPLE DISCUSSION"
    text_content = "Vous avez été assigné à la discussion avec un client.\n\n La conversation sera du type Discussion-Chat, Agissez vite s'il vous plait pour la satisafaction du client!"
    is_simple = True
    if revendeur.email:
        send_html_email(
            subject,
            [revendeur.email],
            "shop/assign_rev_email.html",
            text_content,
            {"conversation": conversation, "is_simple": is_simple},
        )

    return redirect("notifications")


@login_required
def mukubwa_reply(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="mukubwa").exists():
        raise PermissionDenied()

    conversation = notification.conversation
    conversation.participants.add(request.user)

    notification.mark_as_read()

    return redirect("conversation_detail", conversation_id=conversation.id)


@login_required
def revendeur_reply(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="revendeur").exists():
        raise PermissionDenied()

    conversation = notification.conversation
    conversation.participants.add(request.user)

    notification.mark_as_read()

    return redirect("conversation_detail", conversation_id=conversation.id)
