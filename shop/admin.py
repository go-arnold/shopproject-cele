from django.contrib import admin
from .models import Product, Feature, Category, Vente, Testimony, FavoriteProduct, Conversation, Order, OrderItem, Message, Notification


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1


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

    def display_category(self, obj):
        return obj.category
    display_category.short_description = 'Catégorie'

    def display_badge(self, obj):
        return obj.current_badge
    display_badge.short_description = 'Badge actuel'

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
    list_display = ('product', 'utilisateur', 'rating',
                    'short_message', 'date_created')
    search_fields = ('utilisateur__username', 'product__name', 'message')
    list_filter = ('rating', 'date_created')
    raw_id_fields = ('product', 'utilisateur')
    readonly_fields = ('date_created',)

    def short_message(self, obj):
        if not obj.message:
            return ''
        return (obj.message[:80] + '...') if len(obj.message) > 80 else obj.message
    short_message.short_description = 'Message'


@admin.register(FavoriteProduct)
class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ('produit', 'utilisateur', 'date_ajout')
    search_fields = ('utilisateur__username', 'produit__name')
    list_filter = ('date_ajout',)
    raw_id_fields = ('produit', 'utilisateur')
    readonly_fields = ('date_ajout',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_from_cart', 'related_order',
                    'created_at', 'display_name')
    search_fields = ('id', 'related_order__id')
    list_filter = ('is_from_cart', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'created_at', 'status')
    search_fields = ('id', 'user__username')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price')
    search_fields = ('order__id', 'product__name')
    readonly_fields = ()


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'timestamp',
                    'content', 'metadata', 'seen', 'image')
    search_fields = ('conversation__id', 'sender__username', 'content')
    list_filter = ('seen', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'body', 'created_at',
                    'is_read', 'title', 'conversation')
    search_fields = ('user__username', 'message')
    list_filter = ('is_read', 'created_at')
    readonly_fields = ('created_at',)
