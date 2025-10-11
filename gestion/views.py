from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from shop.models import Product, Feature, Category, Vente
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from gestion.decorators import admin_required
from django.http import JsonResponse
from datetime import timedelta
from django.db.models import Sum, F
from django.utils.timezone import now


def is_admin_user(user):
    """Vérifie si l'utilisateur est dans le groupe 'mukubwa' ou 'revendeur'"""
    return user.groups.filter(name__in=['mukubwa', 'revendeur']).exists()

@admin_required
def dashboard(request):
    """Page principale du dashboard"""
    # Statistiques de base
    total_products = Product.objects.count()
    recent_products = Product.objects.order_by('-date_added')[:5]
    today = now().date()
    current_month = today.month
    current_year = today.year

    # --- Données de base ---
    produits = Product.objects.select_related('category_fk')

    produits_mois_courant = produits.filter(
        date_added__month=current_month,
        date_added__year=current_year
    )

    produits_mois_precedent = produits.filter(
        date_added__month=(current_month - 1 if current_month > 1 else 12),
        date_added__year=(current_year if current_month > 1 else current_year - 1)
    )

    # --- a. Croissance potentielle ---
    profit_actuel = produits.aggregate(
        total_profit=Sum(F('price') - F('price_primary'))
    )['total_profit'] or 0

    profit_precedent = produits_mois_precedent.aggregate(
        total_profit=Sum(F('price') - F('price_primary'))
    )['total_profit'] or 0

    croissance_pourcentage = 0
    if profit_precedent > 0:
        croissance_pourcentage = ((profit_actuel - profit_precedent) / profit_precedent) * 100

    # --- b. Revenu attendu (mois courant) ---
    revenu_courant = produits_mois_courant.aggregate(total=Sum('price'))['total'] or 0
    revenu_precedent = produits_mois_precedent.aggregate(total=Sum('price'))['total'] or 0

    revenu_pourcentage = 0
    if revenu_precedent > 0:
        revenu_pourcentage = ((revenu_courant - revenu_precedent) / revenu_precedent) * 100

    # --- c. Revenu quotidien ---
    produits_aujourdhui = produits.filter(date_added__date=today)
    produits_hier = produits.filter(date_added__date=today - timedelta(days=1))

    revenu_jour = produits_aujourdhui.aggregate(total=Sum('price'))['total'] or 0
    revenu_hier = produits_hier.aggregate(total=Sum('price'))['total'] or 0

    revenu_journalier_pourcentage = 0
    if revenu_hier > 0:
        revenu_journalier_pourcentage = ((revenu_jour - revenu_hier) / revenu_hier) * 100

    # --- d. Revenu mensuel attendu (catégorie Habillement) ---
    habits_categories = [
        'Habits/Homme', 'Habits/Femme', 'Habits/Enfants', 'Habits/Souliers'
    ]

    # 🟢 maintenant on filtre uniquement sur Category.name
    habits_mois_courant = produits_mois_courant.filter(category_fk__name__in=habits_categories)
    habits_mois_precedent = produits_mois_precedent.filter(category_fk__name__in=habits_categories)

    revenu_habits_courant = habits_mois_courant.aggregate(total=Sum('price'))['total'] or 0
    revenu_habits_precedent = habits_mois_precedent.aggregate(total=Sum('price'))['total'] or 0

    habits_pourcentage = 0
    if revenu_habits_precedent > 0:
        habits_pourcentage = ((revenu_habits_courant - revenu_habits_precedent) / revenu_habits_precedent) * 100

    # --- Envoi au template ---
    context = {
        'croissance_potentielle': round(profit_actuel, 2),
        'croissance_pourcentage': round(croissance_pourcentage, 2),

        'revenu_mensuel': round(revenu_courant, 2),
        'revenu_mensuel_pourcentage': round(revenu_pourcentage, 2),

        'revenu_quotidien': round(revenu_jour, 2),
        'revenu_quotidien_pourcentage': round(revenu_journalier_pourcentage, 2),

        'revenu_habits': round(revenu_habits_courant, 2),
        'revenu_habits_pourcentage': round(habits_pourcentage, 2),

        'total_products': total_products,
        'recent_products': recent_products,
    }

    return render(request, 'gestion/dashboard1.html', context)

# 🟢 Liste des produits
@admin_required
def admin_products(request):
    """Liste tous les produits avec pagination"""
    products_list = Product.objects.select_related('category_fk').order_by('-date_added')

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        products_list = products_list.filter(name__icontains=search_query)

    # Filtre par catégorie
    category_filter = request.GET.get('category', '')
    if category_filter:
        products_list = products_list.filter(category_fk__id=category_filter)

    # Pagination
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': Category.objects.all(),  # 🔄 récupérées depuis le modèle
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'gestion/admin_products.html', context)


# 🟢 Ajouter un produit
@admin_required
def add_product(request):
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = Category.objects.filter(id=category_id).first()

            product = Product(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                price=request.POST.get('price'),
                price_primary=request.POST.get('price_primary') or None,
                category_fk=category,  # 🔄 liaison via FK
                badge=request.POST.get('badge'),
                rating=request.POST.get('rating', 0),
                reviews=request.POST.get('reviews', 0),
                date_wish=request.POST.get('date_wish'),
            )

            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.full_clean()
            product.save()

            # Ajout des features
            features = request.POST.getlist('features[]')
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(product=product, name=feature_name.strip())

            messages.success(request, f'Le produit "{product.name}" a été ajouté avec succès.')
            return redirect('gestion:admin_products')

        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du produit : {str(e)}')

    context = {
        'categories': Category.objects.all(),  # 🔄 dans le template, ce sera un select dynamique
    }
    return render(request, 'gestion/add_product.html', context)


# 🟢 Modifier un produit
@admin_required
def edit_product(request, product_id):
    """Modifier un produit existant"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = Category.objects.filter(id=category_id).first()

            product.name = request.POST.get('name')
            product.description = request.POST.get('description')
            product.price = request.POST.get('price')
            product.price_primary = request.POST.get('price_primary') or None
            product.category_fk = category
            product.badge = request.POST.get('badge')
            product.rating = request.POST.get('rating', 0)
            product.reviews = request.POST.get('reviews', 0)

            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.full_clean()
            product.save()

            # Supprime les anciennes features avant de recréer
            product.features.all().delete()
            features = request.POST.getlist('features[]')
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(product=product, name=feature_name.strip())

            messages.success(request, f'Le produit "{product.name}" a été modifié avec succès.')
            return redirect('gestion:admin_products')

        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')

    context = {
        'product': product,
        'categories': Category.objects.all(),  # 🔄 liste déroulante
    }
    return render(request, 'gestion/edit_product.html', context)


# 🟢 Supprimer un produit
@admin_required
def delete_product(request, product_id):
    """Supprimer un produit"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Le produit "{product_name}" a été supprimé avec succès.')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('gestion:admin_products')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'gestion/delete_product_partial.html', {'product': product})

    return render(request, 'gestion/delete_product.html', {'product': product})


# 🟢 Voir les détails d’un produit
@admin_required
def view_product(request, product_id):
    """Voir les détails d'un produit"""
    product = get_object_or_404(Product.objects.select_related('category_fk'), id=product_id)

    context = {
        'product': product,
    }
    return render(request, 'gestion/view_product.html', context)


@admin_required
def ajouter_vente(request):
    """Ajouter une vente"""
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

            messages.success(request, f'Vente du produit "{produit.name}" enregistrée avec succès.')
            return redirect('gestion:dashboard')

        except Product.DoesNotExist:
            messages.error(request, "Produit introuvable.")
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')

    # Si GET → afficher le formulaire
    context = {
        'methods': Vente.METHODS_CHOICES,
        'produits': Product.objects.all(),  
    }
    return render(request, 'gestion/ajouter_vente.html', context)



@admin_required
def get_product_details(request, product_id):
    """Retourne les infos du produit (utilisé pour auto-remplir le formulaire de vente)"""
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
    ventes_list = Vente.objects.select_related('produit', 'utilisateur').order_by('-date_achat')
    paginator = Paginator(ventes_list, 15) 
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