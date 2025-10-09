from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from shop.models import Product, Feature
from django.core.paginator import Paginator
from gestion.decorators import admin_required
from django.http import JsonResponse


def is_admin_user(user):
    """Vérifie si l'utilisateur est dans le groupe 'mukubwa' ou 'revendeur'"""
    return user.groups.filter(name__in=['mukubwa', 'revendeur']).exists()

@admin_required
def dashboard(request):
    """Page principale du dashboard"""
    # Statistiques de base
    total_products = Product.objects.count()
    recent_products = Product.objects.order_by('-date_added')[:5]
    
    context = {
        'total_products': total_products,
        'recent_products': recent_products,
    }
    return render(request, 'gestion/dashboard1.html', context)


@admin_required
def admin_products(request):
    """Liste tous les produits avec pagination"""
    products_list = Product.objects.all().order_by('-date_added')
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        products_list = products_list.filter(name__icontains=search_query)
    
    # Filtre par catégorie
    category_filter = request.GET.get('category', '')
    if category_filter:
        products_list = products_list.filter(category=category_filter)
    
    # Pagination
    paginator = Paginator(products_list, 12) 
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'gestion/admin_products.html', context)


@admin_required
def add_product(request):
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        try:
            product = Product(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                price=request.POST.get('price'),
                price_primary=request.POST.get('price_primary') or None,
                category=request.POST.get('category'),
                badge=request.POST.get('badge'),
                rating=request.POST.get('rating', 0),
                reviews=request.POST.get('reviews', 0),
                date_wish=request.POST.get('date_wish'),
            )
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.full_clean() 
            product.save()

            features = request.POST.getlist('features[]')
            for feature_name in features:
                if feature_name.strip():  # Ignorer les features vides
                    Feature.objects.create(
                        product=product,
                        name=feature_name.strip()
                    )
            
            messages.success(request, f'Le produit "{product.name}" a été ajouté avec succès.')
            return redirect('gestion:admin_products')
        
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du produit: {str(e)}')
    
    context = {
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'gestion/add_product.html', context)


@admin_required
def edit_product(request, product_id):
    """Modifier un produit existant"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.description = request.POST.get('description')
            product.price = request.POST.get('price')
            product.price_primary = request.POST.get('price_primary') or None
            product.category = request.POST.get('category')
            product.badge = request.POST.get('badge')
            product.rating = request.POST.get('rating', 0)
            product.reviews = request.POST.get('reviews', 0)
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.full_clean()
            product.save()

            features = request.POST.getlist('features[]')
            for feature_name in features:
                if feature_name.strip():
                    Feature.objects.create(
                        product=product,
                        name=feature_name.strip()
                    )
            
            messages.success(request, f'Le produit "{product.name}" a été modifié avec succès.')
            return redirect('gestion:admin_products')
        
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification: {str(e)}')
    
    context = {
        'product': product,
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'gestion/edit_product.html', context)



@admin_required
def delete_product(request, product_id):
    """Supprimer un produit"""
    product = get_object_or_404(Product, id=product_id)

    # Si POST → suppression
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Le produit "{product_name}" a été supprimé avec succès.')

        # Si suppression depuis la modale (AJAX)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('gestion:admin_products')

    # Si c’est une requête AJAX (modale)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'gestion/delete_product_partial.html', {'product': product})

    # Sinon, affichage complet normal
    return render(request, 'gestion/delete_product.html', {'product': product})



@admin_required
def view_product(request, product_id):
    """Voir les détails d'un produit"""
    product = get_object_or_404(Product, id=product_id)
    
    context = {
        'product': product,
    }
    return render(request, 'gestion/view_product.html', context)


