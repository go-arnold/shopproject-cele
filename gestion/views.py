from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncMonth, TruncDay
import json
from django.shortcuts import render
from django.db.models import Count, Sum
import tempfile
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse
import openpyxl
from django.utils import timezone
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from shop.models import Product, Feature, Category, Vente, Notification, Order, Conversation, Message
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from gestion.decorators import admin_required
from django.http import JsonResponse
from datetime import timedelta, datetime
from django.db.models import Sum, F, DecimalField
from django.utils.timezone import now
from django.db.models.functions import Coalesce
from django.templatetags.static import static


def is_admin_user(user):

    return user.groups.filter(name__in=['mukubwa', 'revendeur']).exists()


@admin_required
def dashboard(request):

    today = now().date()
    current_month = today.month
    current_year = today.year
    notifications = Notification.objects.filter(
        user=request.user).order_by("-created_at")
    notif_count = notifications.count()

    ventes = Vente.objects.select_related('produit', 'produit__category_fk')

    ventes_mois_courant = ventes.filter(
        date_achat__month=current_month, date_achat__year=current_year)
    ventes_mois_precedent = ventes.filter(date_achat__month=(current_month - 1 if current_month > 1 else 12),
                                          date_achat__year=(current_year if current_month > 1 else current_year - 1))

    def calculate_revenue_and_profit(ventes):
        revenue = ventes.aggregate(total_revenue=Sum('price_final'))[
            'total_revenue'] or 0
        profit = ventes.aggregate(total_profit=Sum(
            F('price_final') - F('produit__price_primary'), output_field=DecimalField()))['total_profit'] or 0
        return revenue, profit

    revenu_courant, profit_actuel = calculate_revenue_and_profit(
        ventes_mois_courant)
    revenu_precedent, profit_precedent = calculate_revenue_and_profit(
        ventes_mois_precedent)

    croissance_pourcentage = 0
    if profit_precedent > 0:
        croissance_pourcentage = (
            (profit_actuel - profit_precedent) / profit_precedent) * 100

    ventes_aujourdhui = ventes.filter(date_achat__date=today)
    ventes_hier = ventes.filter(date_achat__date=today - timedelta(days=1))
    revenu_jour = ventes_aujourdhui.aggregate(
        total=Sum('price_final'))['total'] or 0
    revenu_hier = ventes_hier.aggregate(total=Sum('price_final'))['total'] or 0
    revenu_journalier_pourcentage = 0
    if revenu_hier > 0:
        revenu_journalier_pourcentage = (
            (revenu_jour - revenu_hier) / revenu_hier) * 100

    habits_categories = ['Habits/Homme', 'Habits/Femme',
                         'Habits/Enfants', 'Habits/Souliers', 'Habits/Neutre']
    habits_mois_courant = ventes_mois_courant.filter(
        produit__category_fk__name__in=habits_categories)
    habits_mois_precedent = ventes_mois_precedent.filter(
        produit__category_fk__name__in=habits_categories)
    revenu_habits_courant, _ = calculate_revenue_and_profit(
        habits_mois_courant)
    revenu_habits_precedent, _ = calculate_revenue_and_profit(
        habits_mois_precedent)

    habits_pourcentage = 0
    if revenu_habits_precedent > 0:
        habits_pourcentage = (
            (revenu_habits_courant - revenu_habits_precedent) / revenu_habits_precedent) * 100

    methodes_stats = (
        ventes.values('method')
        .annotate(total=Coalesce(Sum('price_final'), 0, output_field=DecimalField()))
        .order_by('method')
    )
    methods_labels = [item['method'] for item in methodes_stats]
    methods_data = [float(item['total']) for item in methodes_stats]

    recent_ventes = ventes.order_by('-date_achat')[:5]
    orders = Order.objects.select_related(
        'user').prefetch_related('items__product')
    qs = Conversation.objects.filter(
        participants=request.user).order_by("-created_at")
    paginator_sms = Paginator(qs, 5)
    paginator_notif = Paginator(notifications, 5)
    paginator_order = Paginator(orders, 10)

    page_sms = request.GET.get('page_sms')
    page_notif = request.GET.get('page_notif')
    page_order = request.GET.get('page_order')

    try:
        page_obj_sms = paginator_sms.page(page_sms)
    except PageNotAnInteger:
        page_obj_sms = paginator_sms.page(1)
    except EmptyPage:
        page_obj_sms = paginator_sms.page(paginator_sms.num_pages)

    try:
        page_obj_order = paginator_order.page(page_order)
    except PageNotAnInteger:
        page_obj_order = paginator_order.page(1)
    except EmptyPage:
        page_obj_order = paginator_order.page(paginator_order.num_pages)

    try:
        page_obj_notif = paginator_notif.page(page_notif)
    except PageNotAnInteger:
        page_obj_notif = paginator_notif.page(1)
    except EmptyPage:
        page_obj_notif = paginator_notif.page(paginator_notif.num_pages)

    conversations_info = []

    for conv in page_obj_sms.object_list:

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

    context = {
        'croissance_potentielle': round(profit_actuel, 2),
        'croissance_pourcentage': round(croissance_pourcentage, 2),
        'revenu_mensuel': round(revenu_courant, 2),
        'revenu_mensuel_pourcentage': round(((revenu_courant - revenu_precedent) / revenu_precedent) * 100 if revenu_precedent > 0 else 0, 2),
        'revenu_quotidien': round(revenu_jour, 2),
        'revenu_quotidien_pourcentage': round(revenu_journalier_pourcentage, 2),
        'revenu_habits': round(revenu_habits_courant, 2),
        'revenu_habits_pourcentage': round(habits_pourcentage, 2),
        'total_ventes': ventes.count(),
        'recent_ventes': recent_ventes,
        'methods_labels': methods_labels,
        'methods_data': methods_data,
        'notif_count': notif_count,


        'page_obj_notif': page_obj_notif,
        'page_obj_order': page_obj_order,
        'page_obj_sms': page_obj_sms,

        'conversations_info': conversations_info,


        'paginator_sms': paginator_sms,
        'page_sms': page_sms,
        'is_paginated_sms': page_obj_sms.has_other_pages(),

        'paginator_notif': paginator_notif,
        'page_notif': page_notif,
        'is_paginated_notif': page_obj_notif.has_other_pages(),

        'paginator_order': paginator_order,
        'page_order': page_order,
        'is_paginated_order': page_obj_order.has_other_pages(),
    }
    return render(request, "gestion/dash.html", context)


@admin_required
def admin_products(request):

    products_list = Product.objects.select_related(
        'category_fk').order_by('-date_added')

    search_query = request.GET.get('search', '')
    if search_query:
        products_list = products_list.filter(name__icontains=search_query)

    category_filter = request.GET.get('category', '')
    if category_filter:
        products_list = products_list.filter(category_fk__id=category_filter)

    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'gestion/admin_products.html', context)


@admin_required
def add_product(request):

    if request.method == 'POST':
        try:

            category_id = request.POST.get('category')
            category = Category.objects.filter(id=category_id).first()

            product = Product(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                long_description=request.POST.get('long_description'),
                chara_entretien=request.POST.get('chara_entretien'),
                delivery_policy_phase1=request.POST.get(
                    'delivery_policy_phase1'),
                delivery_policy_phase2=request.POST.get(
                    'delivery_policy_phase2'),
                price=request.POST.get('price'),
                price_primary=request.POST.get('price_primary') or None,
                price_solde=request.POST.get('price_solde') or None,
                category_fk=category,
                date_wish=request.POST.get('date_wish'),
            )

            if 'image' in request.FILES:
                product.image = request.FILES['image']
            if 'image_one' in request.FILES:
                product.image_one = request.FILES['image_one']
            if 'image_two' in request.FILES:
                product.image_two = request.FILES['image_two']
            if 'image_three' in request.FILES:
                product.image_three = request.FILES['image_three']

            product.full_clean()
            product.save()

            features = request.POST.getlist('features[]')
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(
                        product=product, name=feature_name.strip())

            messages.success(
                request, f'Le produit "{product.name}" a été ajouté avec succès.')
            return redirect('gestion:admin_products')

        except Exception as e:
            messages.error(
                request, f'Erreur lors de l\'ajout du produit : {str(e)}')

    context = {
        'categories': Category.objects.all(),
    }
    return render(request, 'gestion/add_product.html', context)


@admin_required
def edit_product(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        try:

            category_id = request.POST.get('category')
            category = Category.objects.filter(id=category_id).first()

            product.name = request.POST.get('name')
            product.badge = request.POST.get('badge')
            product.description = request.POST.get('description')
            product.long_description = request.POST.get('long_description')
            product.chara_entretien = request.POST.get('chara_entretien')
            product.delivery_policy_phase1 = request.POST.get(
                'delivery_policy_phase1')
            product.delivery_policy_phase2 = request.POST.get(
                'delivery_policy_phase2')
            product.price = request.POST.get('price')
            product.price_primary = request.POST.get('price_primary') or None
            product.price_solde = request.POST.get('price_solde') or None
            product.category_fk = category
            product.date_wish = request.POST.get('date_wish')

            if 'image' in request.FILES:
                product.image = request.FILES['image']
            if 'image_one' in request.FILES:
                product.image_one = request.FILES['image_one']
            if 'image_two' in request.FILES:
                product.image_two = request.FILES['image_two']
            if 'image_three' in request.FILES:
                product.image_three = request.FILES['image_three']

            product.full_clean()
            product.save()

            product.features.all().delete()
            features = request.POST.getlist('features[]')
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(
                        product=product, name=feature_name.strip())

            messages.success(
                request, f'Le produit "{product.name}" a été modifié avec succès.')
            return redirect('gestion:admin_products')

        except Exception as e:
            messages.error(
                request, f'Erreur lors de la modification : {str(e)}')

    context = {
        'product': product,
        'categories': Category.objects.all(),
    }
    return render(request, 'gestion/edit_product.html', context)


@admin_required
def delete_product(request, product_id):

    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(
            request, f'Le produit "{product_name}" a été supprimé avec succès.')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('gestion:admin_products')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'gestion/delete_product_partial.html', {'product': product})

    return render(request, 'gestion/delete_product.html', {'product': product})


@admin_required
def view_product(request, product_id):

    product = get_object_or_404(
        Product.objects.select_related('category_fk'), id=product_id)
    context = {
        'product': product,
    }
    return render(request, 'gestion/view_product.html', context)


@admin_required
def ajouter_vente(request):

    if request.method == 'POST':
        try:
            produit_id = request.POST.get('produit_id')
            date_achat = request.POST.get('date_achat')
            price_final = request.POST.get('price_final') or None
            method = request.POST.get('method', 'Cash')

            produit = Product.objects.get(id=produit_id)

            vente = Vente.objects.create(
                utilisateur=request.user,
                produit=produit,
                date_achat=date_achat,
                price_final=price_final,
                method=method
            )

            messages.success(
                request, f'Vente du produit "{produit.name}" enregistrée avec succès.')
            return redirect('gestion:dashboard')

        except Product.DoesNotExist:
            messages.error(request, "Produit introuvable.")
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    context = {
        'methods': Vente.METHODS_CHOICES,
        'produits': Product.objects.all(),
    }
    return render(request, 'gestion/ajouter_vente.html', context)


@admin_required
def get_product_details(request, product_id):

    try:
        produit = Product.objects.get(id=product_id)
        data = {
            'id': produit.id,
            'name': produit.name,
            'price': float(produit.price),
            'price_primary': float(produit.price_primary or 0),
            'category': produit.category_fk.name if produit.category_fk else '',
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produit introuvable'}, status=404)


@admin_required
def liste_ventes(request):
    utilisateur = request.user
    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes_list = Vente.objects.select_related(
            'produit', 'utilisateur').order_by('-date_achat')
    else:
        ventes_list = Vente.objects.filter(utilisateur=utilisateur).select_related(
            'produit', 'utilisateur').order_by('-date_achat')

    paginator = Paginator(ventes_list, 7)
    page_number = request.GET.get('page')
    ventes = paginator.get_page(page_number)

    return render(request, 'gestion/liste_ventes.html', {
        'ventes': ventes,
    })


@admin_required
def supprimer_vente(request, vente_id):
    vente = get_object_or_404(Vente, id=vente_id)

    if request.method == 'POST':
        vente.delete()
        messages.success(request, "La vente a été supprimée avec succès.")
        return redirect('liste_ventes')

    return render(request, 'gestion/supprimer_vente.html', {'vente': vente})


@admin_required
def modifier_vente(request, vente_id):
    vente = get_object_or_404(Vente, id=vente_id)
    produits = Product.objects.all()

    if request.method == 'POST':
        produit_id = request.POST.get('produit_id')
        price_final = request.POST.get('price_final')
        method = request.POST.get('method')
        date_achat = request.POST.get('date_achat')

        if produit_id:
            vente.produit_id = produit_id
        vente.price_final = price_final or vente.produit.price
        vente.method = method
        vente.date_achat = date_achat
        vente.save()

        messages.success(request, "La vente a été modifiée avec succès.")
        return redirect('gestion:liste_ventes')

    return render(request, 'gestion/modifier_vente.html', {
        'vente': vente,
        'produits': produits,
        'methods': Vente.METHODS_CHOICES,
    })


@admin_required
def liste_ventes_rev(request):
    utilisateur = request.user

    if utilisateur.groups.filter(name="revendeur").exists():
        return redirect('gestion:dashboard')

    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes_list = Vente.objects.select_related(
            'produit', 'utilisateur').order_by('-date_achat')
    else:
        ventes_list = Vente.objects.filter(utilisateur=utilisateur).select_related(
            'produit', 'utilisateur').order_by('-date_achat')

    filtre = request.GET.get('filtre')
    date_achat_search = request.GET.get('date_achat')
    date_enregistrement_search = request.GET.get('date_enregistrement')
    maintenant = timezone.now()

    if filtre == "2":
        ventes_list = ventes_list.filter(
            date_achat__gte=maintenant - timedelta(days=2))
    elif filtre == "7":
        ventes_list = ventes_list.filter(
            date_achat__gte=maintenant - timedelta(days=7))
    elif filtre == "30":
        ventes_list = ventes_list.filter(
            date_achat__gte=maintenant - timedelta(days=30))
    elif filtre == "90":
        ventes_list = ventes_list.filter(
            date_achat__gte=maintenant - timedelta(days=90))

    if date_achat_search:
        try:
            date_obj = datetime.strptime(date_achat_search, "%Y-%m-%d")
            ventes_list = ventes_list.filter(date_achat__date=date_obj)
        except ValueError:
            pass

    if date_enregistrement_search:
        try:
            date_obj = datetime.strptime(
                date_enregistrement_search, "%Y-%m-%d")
            ventes_list = ventes_list.filter(
                date_enregistrement__date=date_obj)
        except ValueError:
            pass

    paginator = Paginator(ventes_list, 7)
    page_number = request.GET.get('page')
    ventes = paginator.get_page(page_number)

    return render(request, 'gestion/liste_ventes_rev.html', {
        'ventes': ventes,
        'filtre': filtre,
    })


@admin_required
def export_ventes_excel(request):
    utilisateur = request.user

    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes = Vente.objects.select_related('produit', 'utilisateur')
    else:
        ventes = Vente.objects.filter(
            utilisateur=utilisateur).select_related('produit', 'utilisateur')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ventes"

    ws.append(["Produit", "Utilisateur", "Prix", "Méthode", "Date"])

    for v in ventes:
        ws.append([
            v.produit_nom,
            v.utilisateur.username,
            float(v.price_final or v.produit_prix),
            v.method,
            v.date_achat.strftime("%Y-%m-%d %H:%M")
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="ventes.xlsx"'
    wb.save(response)

    return response


@admin_required
def export_ventes_pdf(request):
    utilisateur = request.user

    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes = Vente.objects.select_related('produit', 'utilisateur')
    else:
        ventes = Vente.objects.filter(
            utilisateur=utilisateur).select_related('produit', 'utilisateur')
    logo_url = request.build_absolute_uri(static('static-img/logo-white.png'))

    html_string = render_to_string('gestion/pdf_ventes.html', {
        'ventes': ventes,
        'logo_url': logo_url
    })

    html = HTML(string=html_string)

    with tempfile.NamedTemporaryFile(delete=True) as output:
        html.write_pdf(target=output.name)

        pdf_data = output.read()

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ventes.pdf"'
    return response


@csrf_exempt
def dashboard_pdf(request):
    if request.method == "POST":
        data = json.loads(request.body)
        images = data.get("images", [])
        logo_url = request.build_absolute_uri(
            static('static-img/logo-white.png'))

        html_content = f"""
        <html >
        <head >
           <style >
              @page {{
                   size: A4
                    margin: 20mm
                   background-color:  
                   }}
               body {{
                    font-family: Arial, sans-serif
                    background-color:  
                    color: white
                    text-align: center;
                }}
                .logo {{
                    width: 130px
                    margin-bottom: 10px
                }}

                h1 {{
                    text-align: center
                    color:  
                    margin-bottom: 40px
                    font-size: 26px;
                }}

                h2 {{
                    color:  
                    margin-top: 40px
                    margin-bottom: 10px
                    font-size: 20px;
                }}

                .chart-container {{
                    margin-bottom: 40px
                    text-align: center
                }}

                img.chart {{
                    width: 100 %
                    border: 1px solid  
                    border-radius: 8px
                     / * background-color: white; pour éviter que le fond bleu nuit altere les images * /
                }}
            </style >
        </head >
        <body >

            <img src = "{logo_url}" class="logo" />
            <h1 > Dashboard des Ventes</h1>
        """
        titles = [
            "Ventes des 7 derniers jours",
            "Chiffre d'affaires — 12 derniers mois",
            "Répartition des méthodes de paiement",
            "Top 10 des produits vendus",
            "Nombre de ventes par revendeur",
            "Chiffre d'affaires par revendeur",
            "Revenu habillement — 7 derniers jours"
        ]

        for index, img in enumerate(images):
            html_content += f"""
                <div class = "chart-container">
                    <h2 > {titles[index]}</h2>
                    <img class = "chart" src="{img}" />
                </div >
            """

        html_content += """
        </body >
        </html >
        """

        html = HTML(string=html_content)

        with tempfile.NamedTemporaryFile(delete=True) as output_pdf:
            html.write_pdf(output_pdf.name)
            pdf_data = output_pdf.read()

        return HttpResponse(pdf_data, content_type="application/pdf")

    return HttpResponse(status=405)


@admin_required
def dashboard_ventes(request):
    utilisateur = request.user
    today = timezone.now()
    if utilisateur.groups.filter(name="revendeur").exists():
        return redirect('gestion:dashboard')

    if utilisateur.groups.filter(name="mukubwa").exists():
        ventes = Vente.objects.all().select_related('produit', 'utilisateur')
    else:
        ventes = Vente.objects.filter(
            utilisateur=utilisateur).select_related('produit', 'utilisateur')

    last_week = today - timedelta(days=7)
    last_year = today - timedelta(days=365)

    ventes_7j = (
        ventes.filter(date_achat__gte=last_week)
        .annotate(day=TruncDay("date_achat"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    ventes_7j = [
        {"day": item["day"].strftime("%Y-%m-%d"), "total": item["total"]}
        for item in ventes_7j
    ]

    ca_mensuel = (
        ventes.filter(date_achat__gte=last_year)
        .annotate(month=TruncMonth("date_achat"))
        .values("month")
        .annotate(total=Sum("price_final"))
        .order_by("month")
    )

    ca_mensuel = [
        {
            "month": item["month"].strftime("%Y-%m"),
            "total": float(item["total"]) if item["total"] else 0
        }
        for item in ca_mensuel
    ]

    methode_repartition = (
        ventes.values("method")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    methode_repartition = [
        {"method": row["method"], "total": row["total"]}
        for row in methode_repartition
    ]

    top_produits = (
        ventes.values("produit__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    top_produits = [
        {"produit": row["produit__name"], "total": row["total"]}
        for row in top_produits
    ]

    ventes_par_revendeur = (
        ventes.values("utilisateur__username")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    ventes_par_revendeur = [
        {"revendeur": row["utilisateur__username"], "total": row["total"]}
        for row in ventes_par_revendeur
    ]

    ca_par_revendeur = (
        ventes.values("utilisateur__username")
        .annotate(ca_total=Sum("price_final"))
        .order_by("-ca_total")
    )

    ca_par_revendeur = [
        {
            "revendeur": row["utilisateur__username"],
            "total": float(row["ca_total"]) if row["ca_total"] else 0.0
        }
        for row in ca_par_revendeur
    ]

    habits_categories = [
        'Habits/Homme', 'Habits/Femme', 'Habits/Enfants',
        'Habits/Souliers', 'Habits/Neutre'
    ]

    ventes_habillement = (
        ventes.filter(produit__category_fk__name__in=habits_categories)
        .filter(date_achat__gte=last_week)
        .annotate(day=TruncDay("date_achat"))
        .values("day")
        .annotate(total=Sum("price_final"))
        .order_by("day")
    )

    ventes_habillement = [
        {"day": item["day"].strftime(
            "%Y-%m-%d"), "total": float(item["total"])}
        for item in ventes_habillement
    ]

    context = {
        "ventes_7j": json.dumps(ventes_7j),
        "ca_mensuel": json.dumps(ca_mensuel),
        "methode_repartition": json.dumps(methode_repartition),
        "top_produits": json.dumps(top_produits),
        "ventes_par_revendeur": json.dumps(ventes_par_revendeur),
        "ca_par_revendeur": json.dumps(ca_par_revendeur),
        "ventes_habillement": json.dumps(ventes_habillement),
    }

    return render(request, "gestion/graphs.html", context)
