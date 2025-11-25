from django.http import JsonResponse, HttpResponseBadRequest
from .models import Product, FavoriteProduct
from django.shortcuts import get_object_or_404
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max, Count
from django.db import transaction
from .models import Product, Category, Testimony, FavoriteProduct
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
import random
from django.db.models import Q
from .cart import Cart


from django.shortcuts import render


def homeVue(request):
    """Récupère toutes les catégories et rend `shop/homepage.html`.

    Contexte retourné:
    - `categories`: QuerySet de `Category.objects.all()`
    """
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
    """Affiche une catégorie et ses produits.

    Args:
        request: HttpRequest
        pk: primary key (id) de la Category

    Contexte retourné:
    - `category`: instance de Category
    - `products`: QuerySet des produits rattachés
    - `categories`: liste de toutes les catégories (pour navigation)
    """
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

    # Pagination: 12 produits par page
    paginator = Paginator(products_qs, 12)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    # Prix le plus élevé pour cette catégorie
    agg = products_qs.aggregate(max_price=Max('price'))
    most_expensive_price = agg.get('max_price')

    # Catégories similaires: choisir jusqu'à 2 autres catégories
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
    """Affiche tous les produits avec la même pagination que `categoryVue`.

    Contexte retourné (noms identiques à `categoryVue` pour compatibilité):
    - `products`: liste de produits pour la page courante
    - `page_obj`, `paginator`, `is_paginated`, `start_index`, `end_index`, `total_count`
    - `categories`: toutes les catégories (utile pour la navigation)
    """
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

    # Pagination: 12 produits par page (mêmes valeurs et noms que dans categoryVue)
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

    # If we don't have 4 similar products from the same category, fill the rest
    # with random products from the rest of the catalogue (excluding current and
    # already selected products). This ensures `similar_products` contains up to
    # 6 items whenever possible.
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
    """Reçoit un POST depuis le formulaire produit et crée un `Testimony`.

    - Requiert une session utilisateur (redirige vers login si non connecté).
    - Attend `rating` et `message` dans `request.POST`.
    - Redirige vers la page produit après création.
    """
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

    # Preselect all products
    products = Product.objects.all()

    if request.user.is_authenticated:
        favorite_ids = set(
            FavoriteProduct.objects.filter(utilisateur=request.user)
                                   .values_list("produit_id", flat=True)
        )
    else:
        favorite_ids = set()

    # Handle search query
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

    # Pagination
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
    """Un seul endpoint : s'il est favori → enlever. Sinon → ajouter."""
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
    """Rend la page 'À propos'."""
    return render(request, 'shop/about.html')


"""
def cart(request):
    Rend la page du panier.
    return render(request, 'shop/cart.html')"""


def cart_view(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart})


"""
Ancienne vue de listing de produits (conservée en commentaire pour référence):
def product_list(request):
    products = Product.objects.prefetch_related('features').all()

    # Convertir les produits en liste de dictionnaires
    product_data = []
    for p in products:
        product_data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "category": p.category,
            "image": p.image.url if p.image else "",
            "badge": p.badge,
            "features": [f.name for f in p.features.all()],
            "rating": p.rating,
            "reviews": p.reviews
        })

    return render(request, 'shop/home.html', {
        "products": products,
        "product_data": product_data
    })

"""
