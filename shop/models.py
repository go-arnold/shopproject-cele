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
from django.conf import settings
from pgvector.django import VectorField, HnswIndex

User = get_user_model()


def validate_description_length(value):
    min_length = 20
    max_length = 100

    if len(value) < min_length:
        raise ValidationError(
            f"La description doit contenir au moins {min_length} caractères."
        )
    if len(value) > max_length:
        raise ValidationError(
            f"La description ne doit pas dépasser {max_length} caractères."
        )

    if not re.search(
        r"\b(est|avec|permet|offre|dispose|intègre|embarque|équipé)\b",
        value,
        re.IGNORECASE,
    ):
        raise ValidationError(
            "La description doit ressembler à une phrase complète (ex: contenir un verbe)."
        )


def validate_long_description(value):
    sentences = [s for s in re.split(r"[\.\!?]+", value) if s.strip()]
    if len(sentences) > 5:
        raise ValidationError("La description longue ne doit pas dépasser 5 phrases.")


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to="categories/", default="categories/bannerOne_jemfnr.png"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name


class Product(models.Model):
    OLD_CATEGORY_CHOICES = [
        ("Smartphone", "Smartphone"),
        ("Chargeurs", "Chargeurs"),
        ("Audio", "Audio"),
        ("Ordinateurs", "Ordinateurs"),
        ("Montres connectées", "Montres connectées"),
        ("Tablettes", "Tablettes"),
        ("Habits/Homme", "Habits → Homme"),
        ("Habits/Femme", "Habits → Femme"),
        ("Habits/Enfants", "Habits → Enfants"),
        ("Habits/Souliers", "Habits → Souliers"),
    ]

    name = models.CharField(max_length=255)
    description = models.CharField(
        max_length=255, validators=[validate_description_length]
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_primary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    category_fk = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    category_legacy = models.CharField(
        max_length=100, choices=OLD_CATEGORY_CHOICES, default="Smartphone"
    )

    image = models.ImageField(upload_to="produits/", blank=True, null=True)
    badge = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    reviews = models.PositiveIntegerField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_wish = models.DateField(null=True, blank=True)
    price_solde = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    solde_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    image_one = models.ImageField(upload_to="produits/", blank=True, null=True)
    image_two = models.ImageField(upload_to="produits/", blank=True, null=True)
    image_three = models.ImageField(upload_to="produits/", blank=True, null=True)
    long_description = models.TextField(
        blank=True, null=True, validators=[validate_long_description]
    )
    chara_entretien = models.TextField(
        blank=True,
        null=True,
        help_text="Séparez les éléments par des sauts de ligne ou des ';'",
    )
    delivery_policy_phase1 = models.TextField(
        blank=True, null=True, help_text="Phase 1 de la politique de livraison"
    )
    delivery_policy_phase2 = models.TextField(
        blank=True, null=True, help_text="Phase 2 de la politique de livraison"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.price_solde is not None and self.price is not None:
            try:
                price = Decimal(self.price)
                price_solde = Decimal(self.price_solde)
                if price > 0:
                    percent = ((price - price_solde) / price) * Decimal(100)
                    if percent < 0:
                        percent = Decimal("0.00")
                    self.solde_percent = percent.quantize(Decimal("0.01"))
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
        if not self.date_added:
            return self.badge or ""
        try:
            now = timezone.now()
            if now - self.date_added <= timedelta(days=20):
                return "Nouveauté"
        except Exception:
            pass

        return self.badge or ""

    @property
    def chara_entretien_list(self):
        if not self.chara_entretien:
            return []
        items = re.split(r"[\n;]+", self.chara_entretien)
        return [i.strip() for i in items if i.strip()]

    @property
    def average_rating(self):
        agg = self.testimonies.aggregate(avg=Avg("rating"))
        avg = agg.get("avg")
        if avg is None:
            return None
        try:
            return float(round(avg, 2))
        except Exception:
            return float(avg)

    @property
    def reviews_count(self):
        return self.testimonies.count()


class Feature(models.Model):
    product = models.ForeignKey(
        Product, related_name="features", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Testimony(models.Model):
    product = models.ForeignKey(
        Product, related_name="testimonies", on_delete=models.CASCADE
    )
    utilisateur = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=5
    )
    message = models.TextField(max_length=2000)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"

    def __str__(self):
        short = (self.message[:60] + "...") if len(self.message) > 63 else self.message
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
        unique_together = ("utilisateur", "produit")
        verbose_name = "Produit Favori"
        verbose_name_plural = "Produits Favoris"

    def __str__(self):
        return f"{self.utilisateur}  {self.produit.name}"


class Vente(models.Model):
    METHODS_CHOICES = [
        ("OrangeMoney", "Orange Money"),
        ("AirtelMoney", "Airtel Money"),
        ("M-Pesa", "M-Pesa"),
        ("Cash", "Cash"),
    ]

    utilisateur = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, db_index=True
    )
    produit = models.ForeignKey(
        Product, related_name="ventes", on_delete=models.CASCADE, db_index=True
    )
    date_achat = models.DateTimeField(auto_now_add=True, db_index=True)
    price_final = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    method = models.CharField(max_length=50, choices=METHODS_CHOICES, default="Cash")
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

    class Meta:
        indexes = [
            models.Index(fields=['utilisateur', '-date_achat'], name='vente_user_date_idx'),
            models.Index(fields=['produit', '-date_achat'], name='vente_product_date_idx'),
            models.Index(fields=['-date_achat'], name='vente_date_idx'),
            models.Index(fields=['utilisateur', 'date_achat'], name='vente_user_sales_idx'),
        ]
        ordering = ['-date_achat']


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    is_from_cart = models.BooleanField(default=False)
    related_order = models.ForeignKey(
        "Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )

    @property
    def display_name(self):
        if self.is_from_cart and self.related_order:
            return f"Discussion exclusivement sur la commande #{self.related_order.id}"
        return f"Discussion #{self.id} avec agent"

    def __str__(self):
        return f"Conversation {self.id} — {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        indexes = [
            models.Index(fields=['-created_at'], name='conversation_created_idx'),
        ]
        ordering = ['-created_at']


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    metadata = JSONField(null=True, blank=True)
    image = models.ImageField(upload_to="messages/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        if self.content:
            return f"{self.sender}: {self.content[:30]}"
        return f"{self.sender}: [Image]"

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "-timestamp"], name='message_conv_time_idx'),
            models.Index(fields=["sender", "-timestamp"], name='message_sender_time_idx'),
            models.Index(fields=["-timestamp"], name='message_recent_idx'),
        ]
        ordering = ['-timestamp']


class Notification(models.Model):
    TYPE_CHOICES = [
        ("order", "Commande"),
        ("chat", "Discussion"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
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

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at'], name='notification_user_date_idx'),
            models.Index(fields=['-created_at'], name='notification_recent_idx'),
            models.Index(fields=['user', 'is_read'], name='notification_user_read_idx'),
        ]
        ordering = ['-created_at']


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_maker")
    assigned_revendeur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_executer",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = [
        ("attente", "En attente"),
        ("traitement", "Traitement"),
        ("terminé", "Terminé"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="attente")

    def __str__(self):
        return f"Order {self.id} by {self.user}"

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at'], name='order_user_date_idx'),
            models.Index(fields=['assigned_revendeur', '-created_at'], name='order_revendeur_date_idx'),
            models.Index(fields=['status', '-created_at'], name='order_status_date_idx'),
            models.Index(fields=['-created_at'], name='order_recent_idx'),
        ]
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product}"


class ChatLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    user_message = models.TextField()
    bot_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log Chat"
        verbose_name_plural = "Logs Chat"

    def __str__(self):
        return f"{self.user} — {self.created_at:%d/%m/%Y %H:%M}"


class ProductQuestionManager(models.Manager):
    """Custom manager for ProductQuestion analytics."""

    def top_products(self, n=15, days=30):
        """
        Get top N most-asked products in the last N days.

        Returns:
            QuerySet with annotations for question_count and latest_sentiment
        """
        from django.db.models import Count, Q
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)
        return (
            self.filter(
                created_at__gte=cutoff_date,
                product__isnull=False
            )
            .values("product")
            .annotate(
                question_count=Count("id"),
                product_name=models.F("product__name"),
                product_price=models.F("product__price"),
                positive_count=Count("id", filter=Q(sentiment="positive")),
                negative_count=Count("id", filter=Q(sentiment="negative")),
            )
            .order_by("-question_count")[:n]
        )

    def get_analytics_report(self, n=15, days=30):
        """Get analytics report for the last N days with top N products."""
        from django.db.models import Count, Q, Avg
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)

        top_products = self.top_products(n=n, days=days)

        total_questions = self.filter(
            created_at__gte=cutoff_date
        ).count()

        sentiment_dist = self.filter(
            created_at__gte=cutoff_date
        ).values("sentiment").annotate(count=Count("id"))

        language_dist = self.filter(
            created_at__gte=cutoff_date
        ).values("language").annotate(count=Count("id"))

        return {
            "period_days": days,
            "total_questions": total_questions,
            "top_products": list(top_products),
            "sentiment_distribution": {s["sentiment"]: s["count"] for s in sentiment_dist},
            "language_distribution": {l["language"]: l["count"] for l in language_dist},
            "generated_at": timezone.now().isoformat(),
        }


class ProductQuestion(models.Model):
    """
    Track all product-related questions asked via the AI assistant.
    Used to build analytics reports on what products customers ask about.
    """
    objects = ProductQuestionManager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_questions"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions"
    )
    question_text = models.TextField(help_text="The question asked by user")
    response_text = models.TextField(blank=True, help_text="AI assistant response")
    
    # Analytics fields
    language = models.CharField(
        max_length=5,
        default="fr",
        choices=[("fr", "French"), ("en", "English"), ("sw", "Swahili")]
    )
    sentiment = models.CharField(
        max_length=20,
        default="neutral",
        choices=[
            ("positive", "Positive"),
            ("neutral", "Neutral"),
            ("negative", "Negative"),
            ("frustrated", "Frustrated"),
        ]
    )
    keywords = models.JSONField(default=list, help_text="Extracted keywords from question")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"], name="pq_product_date_idx"),
            models.Index(fields=["user", "-created_at"], name="pq_user_date_idx"),
            models.Index(fields=["-created_at"], name="pq_recent_idx"),
            models.Index(fields=["sentiment"], name="pq_sentiment_idx"),
        ]

    def __str__(self):
        return f"Q: {self.question_text[:50]}... ({self.created_at:%Y-%m-%d})"


class ProductEmbedding(models.Model):
    """
    Vector representation of a product, used for RAG retrieval by the AI
    assistant. One row per product; re-embedded whenever the product changes
    (see shop/signals.py -> shop/tasks/embeddings.py).
    """

    EMBEDDING_DIMENSIONS = 768

    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="embedding"
    )
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    embedded_text = models.TextField(
        help_text="Exact text sent to the embedding model, kept for audit/debugging."
    )
    metadata = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=64, default="gemini-embedding-001")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="product_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

    def __str__(self):
        return f"Embedding for {self.product_id}"