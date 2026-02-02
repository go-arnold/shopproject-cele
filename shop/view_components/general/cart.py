from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from utils.cart import Cart
from django.shortcuts import render


@require_POST
@csrf_exempt
def add_to_cart(request):
    cart = Cart(request)
    product_id = request.POST.get("product_id")

    if not product_id:
        return JsonResponse({"error": "Missing product_id"}, status=400)

    cart.add(product_id)
    return JsonResponse({"message": "added", "cart_count": len(cart)})


@require_POST
@csrf_exempt
def update_cart(request):
    cart = Cart(request)
    product_id = request.POST.get("product_id")
    quantity = request.POST.get("quantity")

    if not product_id or quantity is None:
        return JsonResponse({"error": "Missing fields"}, status=400)

    cart.add(product_id, quantity=int(quantity), override_quantity=True)

    return JsonResponse(
        {
            "message": "updated",
            "cart_count": len(cart),
            "total_price": float(cart.get_total_price()),
        }
    )


@require_POST
@csrf_exempt
def remove_from_cart(request):
    cart = Cart(request)
    product_id = request.POST.get("product_id")

    if not product_id:
        return JsonResponse({"error": "Missing product_id"}, status=400)

    cart.remove(product_id)

    return JsonResponse(
        {
            "message": "removed",
            "cart_count": len(cart),
            "total_price": float(cart.get_total_price()),
        }
    )


def cart_view(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart})
