from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Product


from django.shortcuts import render
from .models import Product

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

