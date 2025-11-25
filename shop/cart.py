from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        """
        Initialise le panier en utilisant la session.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def add(self, product_id, quantity=1, override_quantity=False):
        """
        Ajoute un produit au panier ou met à jour sa quantité.
        """
        product = Product.objects.get(id=product_id)
        product_id = str(product_id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        """
        Marque la session comme modifiée.
        """
        self.session.modified = True

    def remove(self, product_id):
        """
        Supprime un produit du panier.
        """
        product_id = str(product_id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        """
        Vide complètement le panier.
        """
        self.session[settings.CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        """
        Permet d'itérer sur les items du panier.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        cart_copy = self.cart.copy()

        for product in products:
            item = cart_copy[str(product.id)]
            item['product'] = product
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Nombre total d'items dans le panier.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calcul du total général.
        """
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )
