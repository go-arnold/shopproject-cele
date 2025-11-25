from .cart import Cart


def cart_counter(request):
    cart = Cart(request)
    return {"cart_count": len(cart)}
