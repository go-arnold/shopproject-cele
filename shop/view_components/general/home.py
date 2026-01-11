from django.shortcuts import render
from shop.models import Product
from shop.models import FavoriteProduct
from django.db.models import Count
from shop.models import Category
from django.contrib.auth import get_user_model

User = get_user_model()


def homeVue(request):
    categories = Category.objects.all()
    new_products = Product.objects.order_by("-date_added")[:9]
    single_product_test = Product.objects.first()
    best_sold_products = Product.objects.annotate(sales_count=Count("ventes")).order_by(
        "-sales_count"
    )[:4]

    if request.user.is_authenticated:
        for p in best_sold_products:
            p.is_favorite = FavoriteProduct.objects.filter(
                utilisateur=request.user, produit=p
            ).exists()
    else:
        for p in best_sold_products:
            p.is_favorite = False
    context = {
        "categories": categories,
        "new_products": new_products,
        "producte": single_product_test,
        "best_sold_products": best_sold_products,
    }
    return render(request, "shop/homepage.html", context)
