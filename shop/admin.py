from django.contrib import admin
from .models import Product, Panier, PanierItem, Feature, Category, Vente, Testimony


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
        'price_solde',
        'solde_percent',
        'display_badge',
        'rating',
        'reviews'
    )
    search_fields = ('name', 'category_legacy', 'category_fk__name')
    list_filter = ('category_fk', 'rating')
    inlines = [FeatureInline]
    readonly_fields = ('solde_percent', 'display_badge', 'date_added')

    # permet d'afficher la catégorie (FK ou legacy)
    def display_category(self, obj):
        return obj.category
    display_category.short_description = 'Catégorie'

    def display_badge(self, obj):
        return obj.current_badge
    display_badge.short_description = 'Badge actuel'

    # Ordre et champs affichés dans le formulaire d'édition
    fields = (
        'name',
        'description',
        'long_description',
        'category_fk',
        'category_legacy',
        'image',
        'image_one',
        'image_two',
        'image_three',
        'price',
        'price_solde',
        'solde_percent',
        'price_primary',
        'badge',
        'display_badge',
        'rating',
        'reviews',
        'date_added',
        'date_wish',
        'chara_entretien',
        'delivery_policy_phase1',
        'delivery_policy_phase2',
    )


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


@admin.register(Testimony)
class TestimonyAdmin(admin.ModelAdmin):
    list_display = ('product', 'utilisateur', 'rating', 'short_message', 'date_created')
    search_fields = ('utilisateur__username', 'product__name', 'message')
    list_filter = ('rating', 'date_created')
    raw_id_fields = ('product', 'utilisateur')
    readonly_fields = ('date_created',)

    def short_message(self, obj):
        if not obj.message:
            return ''
        return (obj.message[:80] + '...') if len(obj.message) > 80 else obj.message
    short_message.short_description = 'Message'
