from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import re
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.db.models import Avg
from django.db.models import JSONField


def validate_description_length(value):
    min_length = 20
    max_length = 100

    if len(value) < min_length:
        raise ValidationError(
            f"La description doit contenir au moins {min_length} caractères.")
    if len(value) > max_length:
        raise ValidationError(
            f"La description ne doit pas dépasser {max_length} caractères.")

    if not re.search(r"\b(est|avec|permet|offre|dispose|intègre|embarque|équipé)\b", value, re.IGNORECASE):
        raise ValidationError(
            "La description doit ressembler à une phrase complète (ex: contenir un verbe).")


def validate_long_description(value):
    """Valide que `long_description` ne dépasse pas 3 phrases."""
    # découpe élémentaire sur ., !, ?
    sentences = [s for s in re.split(r'[\.\!?]+', value) if s.strip()]
    if len(sentences) > 5:
        raise ValidationError(
            "La description longue ne doit pas dépasser 5 phrases.")


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=80, blank=True, null=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name


class Product(models.Model):
    OLD_CATEGORY_CHOICES = [
        ('Smartphone', 'Smartphone'),
        ('Chargeurs', 'Chargeurs'),
        ('Audio', 'Audio'),
        ('Ordinateurs', 'Ordinateurs'),
        ('Montres connectées', 'Montres connectées'),
        ('Tablettes', 'Tablettes'),
        ('Habits/Homme', 'Habits → Homme'),
        ('Habits/Femme', 'Habits → Femme'),
        ('Habits/Enfants', 'Habits → Enfants'),
        ('Habits/Souliers', 'Habits → Souliers'),
    ]

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, validators=[
                                   validate_description_length])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_primary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    category_fk = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products'
    )
    category_legacy = models.CharField(
        max_length=100, choices=OLD_CATEGORY_CHOICES, default='Smartphone'
    )

    image = models.ImageField(upload_to="produits/", blank=True, null=True)
    badge = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField()
    reviews = models.PositiveIntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_wish = models.DateField(null=True, blank=True)
    price_solde = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    solde_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    image_one = models.ImageField(upload_to="produits/", blank=True, null=True)
    image_two = models.ImageField(upload_to="produits/", blank=True, null=True)
    image_three = models.ImageField(
        upload_to="produits/", blank=True, null=True)
    long_description = models.TextField(blank=True, null=True, validators=[
                                        validate_long_description])
    chara_entretien = models.TextField(
        blank=True, null=True, help_text="Séparez les éléments par des sauts de ligne ou des ';'")
    delivery_policy_phase1 = models.TextField(
        blank=True, null=True, help_text="Phase 1 de la politique de livraison")
    delivery_policy_phase2 = models.TextField(
        blank=True, null=True, help_text="Phase 2 de la politique de livraison")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Calcul automatique du pourcentage de solde si `price_solde` est renseigné
        if self.price_solde is not None and self.price is not None:
            try:
                price = Decimal(self.price)
                price_solde = Decimal(self.price_solde)
                if price > 0:
                    percent = ((price - price_solde) / price) * Decimal(100)
                    # éviter pourcentage négatif si price_solde > price
                    if percent < 0:
                        percent = Decimal('0.00')
                    # arrondir à 2 décimales
                    self.solde_percent = percent.quantize(Decimal('0.01'))
                else:
                    self.solde_percent = None
            except (InvalidOperation, TypeError):
                self.solde_percent = None
        else:
            self.solde_percent = None

        super().save(*args, **kwargs)

    @property
    def category(self):
        if self.category_fk:
            return self.category_fk.name
        return self.category_legacy

    @property
    def current_badge(self):
        """
        Badge automatique: renvoie 'Nouveauté' pendant les 20 premiers jours
        après la date de création (`date_added`). Ne dépend pas des modifications.
        """
        if not self.date_added:
            return self.badge or ''
        try:
            now = timezone.now()
            if now - self.date_added <= timedelta(days=20):
                return 'Nouveauté'
        except Exception:
            pass
        # Si on veut utiliser la valeur de la base si elle existe
        return self.badge or ''

    @property
    def chara_entretien_list(self):
        """Retourne une liste préparée à partir de `chara_entretien` (split par nouvelle ligne ou ';')."""
        if not self.chara_entretien:
            return []
        items = re.split(r'[\n;]+', self.chara_entretien)
        return [i.strip() for i in items if i.strip()]

    @property
    def average_rating(self):
        """Moyenne des notes provenant des témoignages liés au produit.

        Retourne un float arrondi à 2 décimales ou `None` si pas d'avis.
        """
        agg = self.testimonies.aggregate(avg=Avg('rating'))
        avg = agg.get('avg')
        if avg is None:
            return None
        try:
            return float(round(avg, 2))
        except Exception:
            return float(avg)

    @property
    def reviews_count(self):
        """Nombre total de témoignages liés au produit."""
        return self.testimonies.count()


class Feature(models.Model):
    product = models.ForeignKey(
        Product, related_name='features', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Testimony(models.Model):
    """Témoignage utilisateur lié à un `Product`.

    Attributs principaux:
    - `product`: produit concerné
    - `utilisateur`: auteur (FK vers user)
    - `rating`: note entière (1-5)
    - `message`: texte du témoignage
    - `date_created`: horodatage de création
    """
    product = models.ForeignKey(
        Product, related_name='testimonies', on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    message = models.TextField(max_length=2000)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"

    def __str__(self):
        short = (self.message[:60] +
                 '...') if len(self.message) > 63 else self.message
        return f"{self.utilisateur} — {self.product.name} ({self.rating}) : {short}"


class FavoriteProduct(models.Model):
    utilisateur = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="favoris"
    )
    produit = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="favoris"
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'produit')
        verbose_name = "Produit Favori"
        verbose_name_plural = "Produits Favoris"

    def __str__(self):
        return f"{self.utilisateur}  {self.produit.name}"


class Vente(models.Model):
    METHODS_CHOICES = [
        ('OrangeMoney', 'Orange Money'),
        ('AirtelMoney', 'Airtel Money'),
        ('M-Pesa', 'M-Pesa'),
        ('Cash', 'Cash'),
    ]

    utilisateur = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    produit = models.ForeignKey(
        Product, related_name="ventes", on_delete=models.CASCADE)
    date_achat = models.DateTimeField(auto_now_add=True)
    price_final = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    method = models.CharField(
        max_length=50, choices=METHODS_CHOICES, default='Cash')
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    vendu_a = models.TextField(null=True, blank=True, max_length=50)

    def __str__(self):
        return f"Vente de {self.produit.name} par {self.utilisateur}"

    @property
    def produit_nom(self):
        return self.produit.name

    @property
    def produit_prix(self):
        return self.produit.price

    @property
    def produit_prix_primaire(self):
        return self.produit.price_primary

    @property
    def produit_categorie(self):
        return self.produit.category


User = get_user_model()


class Conversation(models.Model):
    """
    Une conversation entre 2 ou plusieurs utilisateurs :
    - un client
    - un revendeur
    - un 'mukubwa'
    """

    participants = models.ManyToManyField(User, related_name="conversations")

    created_at = models.DateTimeField(auto_now_add=True)

    # Pour savoir si elle a été créée via le panier
    is_from_cart = models.BooleanField(default=False)

    # Optionnel : lien direct vers la commande — utile pour la suite
    related_order = models.ForeignKey(
        'Order', on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations"
    )

    @property
    def display_name(self):
        if self.is_from_cart and self.related_order:
            return f"Concernant la commande #{self.related_order.id}"
        return f"Discussion #{self.id} avec agent"

    def __str__(self):
        return f"Conversation {self.id} — {self.created_at.strftime('%Y-%m-%d')}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    metadata = JSONField(null=True, blank=True)
    image = models.ImageField(upload_to="messages/",
                              blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        if self.content:
            return f"{self.sender}: {self.content[:30]}"
        return f"{self.sender}: [Image]"

    class Meta:
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender']),
        ]


class Notification(models.Model):
    TYPE_CHOICES = [
        ("order", "Commande"),
        ("chat", "Discussion"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications")
    conversation = models.ForeignKey("Conversation", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_order_assigned = models.BooleanField(default=False)

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def __str__(self):
        return f"Notif to {self.user} — {self.title}"


# =========================
#   ORDER / ORDER ITEMS
# =========================

class Order(models.Model):
    """
    Représente le contenu du panier à l'instant où le client clique sur
    'Passer à la discussion'. Geler le panier est ESSENTIEL.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'Traitement'),
        ('done', 'Terminé')
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )

    def __str__(self):
        return f"Order {self.id} by {self.user}"


class OrderItem(models.Model):
    """
    Produit appartenant à une commande.
    """

    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product}"
