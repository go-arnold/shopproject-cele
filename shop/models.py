from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re


def validate_description_length(value):
    min_length = 20
    max_length = 100

    if len(value) < min_length:
        raise ValidationError(f"La description doit contenir au moins {min_length} caractères.")
    if len(value) > max_length:
        raise ValidationError(f"La description ne doit pas dépasser {max_length} caractères.")

    if not re.search(r"\b(est|avec|permet|offre|dispose|intègre|embarque|équipé)\b", value, re.IGNORECASE):
        raise ValidationError("La description doit ressembler à une phrase complète (ex: contenir un verbe).")


class Product(models.Model):
    CATEGORY_CHOICES = [
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
    description = models.CharField(max_length=255, validators=[validate_description_length])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    price_primary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Smartphone')
    image = models.ImageField(upload_to="produits/", blank=True, null=True)
    badge = models.CharField(max_length=100, blank=True, null=True)
    rating = models.FloatField()
    reviews = models.PositiveIntegerField()
    
    date_added = models.DateTimeField(auto_now_add=True)  
    date_wish = models.DateField(null=True, blank=True)  

    def __str__(self):
        return self.name


class Feature(models.Model):
    product = models.ForeignKey(Product, related_name='features', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Panier(models.Model):
    utilisateur = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Panier de {self.utilisateur}"

    @property
    def total(self):
        return sum(item.sous_total for item in self.items.all())


class PanierItem(models.Model):
    panier = models.ForeignKey(Panier, related_name="items", on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantite} x {self.produit.name}"

    @property
    def sous_total(self):
        return self.produit.price * self.quantite
