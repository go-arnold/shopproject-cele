from django.contrib import admin
from .models import Product, Panier, PanierItem, Feature

admin.site.register(Panier)
admin.site.register(PanierItem)

class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'rating', 'reviews')
    inlines = [FeatureInline]


