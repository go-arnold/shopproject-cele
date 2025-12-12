from django.templatetags.static import static
from .utils import send_html_email
from datetime import datetime
from django.utils import timezone
from django.utils.timesince import timesince
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, OrderItem, Conversation, Message, Notification, Product
from django.http import Http404, HttpResponseForbidden
from django.contrib.auth.models import Group
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Product, FavoriteProduct
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max, Count
from django.db import transaction
from .models import Product, Category, Testimony, FavoriteProduct
from django.contrib.auth.decorators import login_required
import random
from django.db.models import Q
from .cart import Cart
from django.contrib.auth import get_user_model
User = get_user_model()


def homeVue(request):
    
    categories = Category.objects.all()
    new_products = Product.objects.order_by('-date_added')[:9]
    single_product_test = Product.objects.first()
    best_sold_products = (
        Product.objects
        .annotate(sales_count=Count('ventes'))
        .order_by('-sales_count')[:4]
    )

    if request.user.is_authenticated:
        for p in best_sold_products:
            p.is_favorite = FavoriteProduct.objects.filter(
                utilisateur=request.user,
                produit=p
            ).exists()
    else:
        for p in best_sold_products:
            p.is_favorite = False
    context = {
        'categories': categories,
        'new_products': new_products,
        'producte': single_product_test,
        'best_sold_products': best_sold_products,
    }
    return render(request, 'shop/homepage.html', context)


def categoryVue(request, pk):
    
    category = get_object_or_404(Category, pk=pk)
    products_qs = category.products.select_related(
        'category_fk').prefetch_related('features').all().order_by('-id')

    if request.user.is_authenticated:
        user_favs = set(
            FavoriteProduct.objects
            .filter(utilisateur=request.user, produit__in=products_qs)
            .values_list('produit_id', flat=True)
        )

        for p in products_qs:
            p.is_favorite = p.id in user_favs

    else:
        for p in products_qs:
            p.is_favorite = False

    
    paginator = Paginator(products_qs, 12)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    
    agg = products_qs.aggregate(max_price=Max('price'))
    most_expensive_price = agg.get('max_price')

    
    similar_qs = (
        Category.objects
        .exclude(pk=category.pk)
        .annotate(prod_count=Count('products'))
        .order_by('-prod_count')
    )[:10]
    similar_qs = list(similar_qs)
    similar_category_one = None
    similar_category_two = None

    if len(similar_qs) >= 2:
        similar_category_one, similar_category_two = random.sample(
            similar_qs, 2)
    elif len(similar_qs) == 1:
        similar_category_one = similar_qs[0]
    context = {
        'category': category,
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': paginator.count,
        'categories': categories,
        'most_expensive_price': most_expensive_price,
        'similar_category_one': similar_category_one,
        'similar_category_two': similar_category_two,
    }
    return render(request, 'shop/category.html', context)


def allProducts(request):
    
    products_qs = Product.objects.select_related('category_fk').prefetch_related(
        'features').all()  

    if request.user.is_authenticated:
        for p in products_qs:
            p.is_favorite = FavoriteProduct.objects.filter(
                utilisateur=request.user,
                produit=p
            ).exists()
    else:

        for p in products_qs:
            p.is_favorite = False

    paginator = Paginator(products_qs, 12)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    context = {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': paginator.count,
        'categories': categories,
    }
    return render(request, 'shop/allProducts.html', context)


def productVue(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.user.is_authenticated:
        product.is_favorite = FavoriteProduct.objects.filter(
            utilisateur=request.user,
            produit=product
        ).exists()
    else:
        product.is_favorite = False

    rat = (
        product.average_rating
        if hasattr(product, 'average_rating') and product.average_rating is not None
        else (product.rating or "0")
    )

    rating = float(str(rat).replace(",", "."))

    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half

    features = [f.name for f in product.features.all()]

    product_data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'price_primary': product.price_primary,
        'category': product.category,
        'image': product.image.url if product.image else '',
        'badge': product.badge,
        'current_badge': product.current_badge,
        'features': features,


        'rating': rat,
        'reviews': product.reviews_count if hasattr(product, 'reviews_count') else (product.reviews or 0),
        'date_added': product.date_added,
        'long_description': product.long_description,
        'chara_entretien_list': product.chara_entretien_list,
        'price_solde': product.price_solde,
        'solde_percent': product.solde_percent,
        'image_one': product.image_one.url if product.image_one else '',
        'image_two': product.image_two.url if product.image_two else '',
        'image_three': product.image_three.url if product.image_three else '',


        "stars": {
            "full": range(full),
            "half": range(half),
            "empty": range(empty),
        }
    }

    categories = Category.objects.all()

    testimonies_qs = product.testimonies.select_related(
        'utilisateur').order_by('-date_created')
    for t in testimonies_qs:
        full = int(t.rating)
        half = 1 if (t.rating - full) >= 0.5 else 0
        empty = 5 - full - half

        t.stars = {
            "full": range(full),
            "half": range(half),
            "empty": range(empty),
        }

    similar_qs = Product.objects.filter(
        category_fk=product.category_fk).exclude(pk=product.pk)
    similar_available_count = similar_qs.count()
    similar_products = []
    similar_products_count = 0
    similar_pks = list(similar_qs.values_list('pk', flat=True))
    sampled_pks = []
    if similar_pks:
        sample_count = min(6, len(similar_pks))
        sampled_pks = random.sample(similar_pks, sample_count)
        similar_products = list(Product.objects.filter(pk__in=sampled_pks))

    
    
    
    
    if len(similar_products) < 6:
        needed = 6 - len(similar_products)
        other_qs = Product.objects.exclude(pk=product.pk)
        if sampled_pks:
            other_qs = other_qs.exclude(pk__in=sampled_pks)
        other_pks = list(other_qs.values_list('pk', flat=True))
        if other_pks:
            add_count = min(needed, len(other_pks))
            sampled_other = random.sample(other_pks, add_count)
            additional = list(Product.objects.filter(pk__in=sampled_other))
            similar_products.extend(additional)

    similar_products_count = len(similar_products)

    return render(request, 'shop/product.html', {
        'product': product,
        'product_data': product_data,
        'categories': categories,
        'testimonies': testimonies_qs,
        'similar_products': similar_products,
        'similar_products_count': similar_products_count,
        'similar_available_count': similar_available_count,
    })


@login_required
def add_testimony(request, pk):
    
    product = get_object_or_404(Product, pk=pk)
    if request.method != 'POST':
        return redirect('product_detail', pk=product.pk)

    rating = request.POST.get('rating')
    message = request.POST.get('message', '').strip()

    if not message:
        return redirect('product_detail', pk=product.pk)

    try:
        rating_val = int(rating)
    except (TypeError, ValueError):
        rating_val = 5

    rating_val = max(1, min(5, rating_val))
    with transaction.atomic():
        Testimony.objects.filter(
            product=product, utilisateur=request.user).delete()
        Testimony.objects.create(
            product=product,
            utilisateur=request.user,
            rating=rating_val,
            message=message,
        )

    return redirect('product_detail', pk=product.pk)


def results(request):
    query = request.GET.get("q", "").strip()

    
    products = Product.objects.all()

    if request.user.is_authenticated:
        favorite_ids = set(
            FavoriteProduct.objects.filter(utilisateur=request.user)
                                   .values_list("produit_id", flat=True)
        )
    else:
        favorite_ids = set()

    
    if query:
        keywords = query.split()
        q_object = Q()

        for word in keywords:
            q_object &= (
                Q(name__icontains=word) |
                Q(description__icontains=word) |
                Q(long_description__icontains=word) |
                Q(category_legacy__icontains=word) |
                Q(category_fk__name__icontains=word)
            )

        products = products.filter(q_object).distinct()

    
    paginator = Paginator(products, 12)
    page_num = request.GET.get("page")

    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    for p in page_obj:
        p.is_favorite = p.id in favorite_ids

    return render(request, "shop/results.html", {
        'query': query,
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': paginator.count,
    })


@login_required
def add_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    fav, created = FavoriteProduct.objects.get_or_create(
        utilisateur=request.user,
        produit=product
    )
    return JsonResponse({"added": True})


@login_required
def remove_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    FavoriteProduct.objects.filter(
        utilisateur=request.user,
        produit=product
    ).delete()
    return JsonResponse({"removed": True})


@login_required
def toggle_favorite(request, product_id):
    
    if request.method != "POST":
        return HttpResponseBadRequest("Méthode invalide")

    product = get_object_or_404(Product, id=product_id)

    fav = FavoriteProduct.objects.filter(
        utilisateur=request.user,
        produit=product
    )

    if fav.exists():
        fav.delete()
        return JsonResponse({"favori": False})

    else:
        FavoriteProduct.objects.create(
            utilisateur=request.user,
            produit=product
        )
        return JsonResponse({"favori": True})


@login_required
def favorites_list(request):
    favoris = FavoriteProduct.objects.filter(
        utilisateur=request.user
    ).select_related("produit")

    products = [fav.produit for fav in favoris]
    for p in products:
        p.is_favorite = FavoriteProduct.objects.filter(
            utilisateur=request.user,
            produit=p
        ).exists()

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': paginator.count,
    }

    return render(request, "shop/favorite.html", context)


def aboutUs(request):
    
    return render(request, 'shop/about.html')


def assistant(request):
    now = timezone.now()

    target = timezone.make_aware(datetime(now.year, 1, 18))
    if now > target:

        target = timezone.make_aware(datetime(now.year + 1, 1, 18))

    remaining = target - now

    days = remaining.days
    seconds = remaining.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return render(request, "shop/assistant.html", {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": secs,
    })


def profile(request):
    if not request.user.is_authenticated:
        return render(request, 'shop/login_required.html')
    return render(request, 'shop/profile.html')


def messages(request):
    html_to_render2 = "shop/login_required.html"

    if not request.user.is_authenticated:
        return render(request, html_to_render2)
    return render(request, 'shop/conversations.html')


def cart_view(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart})


@login_required
def start_conversation_from_cart(request):
    

    cart = Cart(request)

    if len(cart) == 0:
        raise Http404("Votre panier est vide.")

    
    order = Order.objects.create(
        user=request.user,
        total_price=cart.get_total_price(),
    )

    
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            quantity=item["quantity"],
            unit_price=item["price"],
        )

    
    conversation = Conversation.objects.create(
        is_from_cart=True,
        related_order=order
    )
    conversation.participants.add(request.user)

    
    lines = []
    lines.append("Bonjour, je voudrais passer cette commande :\n")
    total = 0

    for item in cart:
        qty = item["quantity"]
        price = item["price"]
        name = item["product"].name
        subtotal = qty * price
        total += subtotal
        lines.append(f"- {name} × {qty} = {subtotal} $")
        item['line'] = f"{name} × {qty} = {subtotal} $"
        item['subtotal'] = subtotal

    lines.append(f"\nTotal : {total} $")

    auto_message = "\n".join(lines)

    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=auto_message,
        metadata={"generated_from_cart": True},
    )

    
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
            title="Nouvelle commande",
            type="order",
            body=f"{request.user} a envoyé une demande d'achat.",
            conversation=conversation
        )

    

    subject = "[ CELEBOBO-BUSINESS ] Nouvelle Commande Client"
    template_name = "shop/email_notify_mukubwa.html"
    text_content = f"{request.user} a envoyé une demande d'achat.\n\n\n {auto_message} \n\n Notification générée automatiquement par votre système"
    context = {
        "auto_message": auto_message,
        "logo_url": request.build_absolute_uri(static('static-img/logo-white.png')),
        "cart": cart,
        "total": total
    }
    if isinstance(recipients, str):
        recipients = [recipients]
    try:
        send_html_email(subject, recipients, template_name,
                        text_content, context)
        print("Email envoyé avec succès à:", recipients)
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

    
    cart.clear()

    
    return redirect("conversation_detail", conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    
    conversation = get_object_or_404(Conversation, id=conversation_id)

    
    if request.user not in conversation.participants.all():
        conversation.participants.add(request.user)

    messages = Message.objects.filter(
        conversation=conversation).order_by("timestamp")

    return render(request, "shop/discussions.html", {
        "conversation": conversation,
        "messages": messages,
        "conversation_name": conversation.display_name,
        "id_id": conversation.id
    })


@login_required
def conversation_messages_json(request, conversation_id):
    
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        return JsonResponse({"error": "Access denied"}, status=403)

    messages = Message.objects.filter(
        conversation=conversation).order_by("timestamp")

    data = []
    for m in messages:
        data.append({
            "id": m.id,
            "sender_id": m.sender.id,
            "sender_name": m.sender.username,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
            "is_me": (m.sender == request.user),
        })

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

        is_first = Message.objects.filter(
            conversation=conversation).count() == 1

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
                    type="chat"
                )
            subject = f"[ CELEBOBO-BUSINESS ] Nouvelle Discussion demandée par un {request.user}"
            template_name = "shop/email_notify_mukubwa.html"
            text_content = f"{request.user} a envoyé une demande d'achat.\n\n\n {msg.content} \n\n Notification générée automatiquement par votre système"
            context = {
                "logo_url": request.build_absolute_uri(static('static-img/logo-white.png')),
                "msg": msg,
                "yes": True

            }
            if isinstance(recipients, str):
                recipients = [recipients]
            try:
                send_html_email(subject, recipients, template_name,
                                text_content, context)
                print("Email envoyé avec succès à:", recipients)
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'email : {e}")

    return JsonResponse({
        "id": msg.id,
        "sender_id": msg.sender.id,
        "content": msg.content,
        "image_url": msg.image.url if msg.image else None,
        "timestamp": msg.timestamp.isoformat(),
        "is_me": True,
    })


@login_required
def fetch_new_messages_ajax(request, conversation_id):
    last_id = int(request.GET.get("last_id", 0))

    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        return JsonResponse({"error": "Access denied"}, status=403)

    new_messages = Message.objects.filter(
        conversation=conversation,
        id__gt=last_id
    ).order_by("timestamp")

    data = []
    for m in new_messages:
        data.append({
            "id": m.id,
            "sender_id": m.sender.id,
            "sender_name": m.sender.username,
            "content": m.content,
            "image_url": m.image.url if m.image else None,
            "timestamp": m.timestamp.isoformat(),
            "is_me": (m.sender == request.user),
        })

    return JsonResponse({"messages": data})


@login_required
def notifications_view(request):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user not in rev and user not in muk:
        raise PermissionDenied()
    else:
        
        notifications = Notification.objects.filter(
            user=user).order_by("-created_at")
        notif_count = int(notifications.count())

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
        page = request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return render(request, "shop/mukubwa_revendeur.html", {
            "notifications": page_obj.object_list,
            "revendeurs": revendeurs,
            "mukubwas": mukubwas,
            "s_users": s_users,
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': page_obj.has_other_pages(),
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
            'total_count': paginator.count,
        })


@login_required
def assign_revendeur(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="mukubwa").exists():
        return HttpResponseForbidden("Accès refusé")

    revendeur_id = request.POST.get("revendeur_id")

    if not revendeur_id:
        messages.error(request, "Veuillez sélectionner un revendeur.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    revendeur = get_object_or_404(User, id=revendeur_id)

    conversation = notification.conversation
    conversation.participants.add(revendeur)

    Notification.objects.filter(
        conversation=conversation,
        user__groups__name="mukubwa",
        type="order"
    ).update(is_order_assigned=True)

    Notification.objects.create(
        user=revendeur,
        conversation=conversation,
        type="order",
        title="Assignation de commande",
        body=f"Vous avez été assigné à la commande 
    )
    subject = "[CELEBOBO-BUSINESS] NOUVELLE ASSIGNATION- UNE COMMANDE"
    text_content = f"Vous avez été assigné à la commande 
    if revendeur.email:
        send_html_email(subject, [revendeur.email], "shop/assign_rev_email.html",
                        text_content, {"conversation": conversation, })

    return redirect("notifications")


@login_required
def assign_revendeur_discussion(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="mukubwa").exists():
        return HttpResponseForbidden("Accès refusé")

    revendeur_id = request.POST.get("revendeur_id")

    if not revendeur_id:
        messages.error(request, "Veuillez sélectionner un revendeur.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    revendeur = get_object_or_404(User, id=revendeur_id)

    conversation = notification.conversation
    conversation.participants.add(revendeur)

    Notification.objects.filter(
        conversation=conversation,
        user__groups__name="mukubwa",
        type="chat"
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
        send_html_email(subject, [revendeur.email], "shop/assign_rev_email.html",
                        text_content, {"conversation": conversation, "is_simple": is_simple})

    return redirect("notifications")


@login_required
def mukubwa_reply(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="mukubwa").exists():
        return HttpResponseForbidden("Accès refusé")

    conversation = notification.conversation
    conversation.participants.add(request.user)

    notification.mark_as_read()

    return redirect("conversation_detail", conversation_id=conversation.id)


@login_required
def revendeur_reply(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if not request.user.groups.filter(name="revendeur").exists():
        return HttpResponseForbidden("Accès refusé")

    conversation = notification.conversation
    conversation.participants.add(request.user)

    notification.mark_as_read()

    return redirect("conversation_detail", conversation_id=conversation.id)


@login_required
def list_conversations(request):
    
    q = request.GET.get("q", "").strip()

    
    qs = Conversation.objects.filter(
        participants=request.user).order_by("-created_at")

    paginator = Paginator(qs, 8)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    
    conversations_info = []
    for conv in page_obj.object_list:
        
        
        last_msg = Message.objects.filter(
            conversation=conv).order_by("-timestamp").first()
        last_content = last_msg.content if last_msg else ""
        last_sender = last_msg.sender if last_msg else None
        last_timestamp = last_msg.timestamp if last_msg else None

        
        others = conv.participants.exclude(id=request.user.id)
        other = others.first() if others.exists() else None

        conversations_info.append({
            "conversation": conv,
            "other": other,
            "last_content": last_content,
            "last_sender": last_sender,
            "last_timestamp": last_timestamp,
        })
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
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': paginator.count,
    }
    return render(request, "shop/list_discussions.html", context)


@login_required
def conversation_new(request):

    existing_convs = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        msg_count=Count('messages')
    ).filter(
        msg_count=0
    )
    if existing_convs.exists():
        return redirect('conversation_detail', conversation_id=existing_convs.first().id)

    conv = Conversation.objects.create(
        is_from_cart=False,
        related_order=None
    )

    return redirect('conversation_detail', conversation_id=conv.id)


def disc(request):
    return render(request, 'shop/list_discussions.html')
