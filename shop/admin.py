from django.contrib import admin
from .models import Product, Panier, PanierItem, Feature, Category, Vente


# --- Catégories ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


# --- Panier et Items ---
admin.site.register(Panier)
admin.site.register(PanierItem)


# --- Features en inline ---
class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1


# --- Produits ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'display_category',
        'price',
        'rating',
        'reviews'
    )
    search_fields = ('name', 'category_legacy', 'category_fk__name')
    list_filter = ('category_fk', 'rating')
    inlines = [FeatureInline]

    # permet d'afficher la catégorie (FK ou legacy)
    def display_category(self, obj):
        return obj.category
    display_category.short_description = 'Catégorie'


# --- Ventes ---
@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = (
        'produit_nom',
        'utilisateur',
        'produit_categorie',
        'produit_prix',
        'price_final',
        'date_achat',
        'method',
    )
    list_filter = ('date_achat', 'utilisateur', 'produit__category_fk')
    search_fields = ('produit__name', 'utilisateur__username')
    readonly_fields = ('date_achat',)
    ordering = ('-date_achat',)
