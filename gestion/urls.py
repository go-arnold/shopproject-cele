from django.urls import path
# from . import views

from gestion.views_components.dashboard import (
    home,
    ventes as dash_ventes,
    export_pdf as exp_pdf,
    discussions,
    invites,
)
from gestion.views_components.produits import ajouter, modifier, supprimer, details
from gestion.views_components.ventes import (
    ajouter as ajouter_v,
    export_excel,
    export_pdf,
    liste,
    modifier as mod_v,
    supprimer as supp_v,
)

app_name = "gestion"

urlpatterns = [
    path("", home.dashboard, name="dashboard"),
    path("produits/", details.admin_products, name="admin_products"),
    path("produits/ajouter/", ajouter.add_product, name="add_product"),
    path(
        "produits/<int:product_id>/modifier/",
        modifier.edit_product,
        name="edit_product",
    ),
    path(
        "produits/<int:product_id>/supprimer/",
        supprimer.delete_product,
        name="delete_product",
    ),
    path("produits/<int:product_id>/", details.view_product, name="view_product"),
    path("ventes/", liste.liste_ventes, name="liste_ventes"),
    path("ventes_rev/", liste.liste_ventes_rev, name="liste_ventes_rev"),
    path("ventes/ajouter/", ajouter_v.ajouter_vente, name="ajouter_vente"),
    path(
        "bulk-vente/", ajouter_v.bulk_enregistrer_vente, name="bulk_enregistrer_vente"
    ),
    path(
        "api/orders/search/",
        ajouter_v.search_orders_by_user,
        name="search_orders_by_user",
    ),
    path(
        "ventes/<int:vente_id>/modifier/", mod_v.modifier_vente, name="modifier_vente"
    ),
    path(
        "ventes/<int:vente_id>/supprimer/",
        supp_v.supprimer_vente,
        name="supprimer_vente",
    ),
    path(
        "produit/<int:product_id>/details/",
        details.get_product_details,
        name="get_product_details",
    ),
    path(
        "ventes/export/excel/",
        export_excel.export_ventes_excel,
        name="export_ventes_excel",
    ),
    path("ventes/export/pdf/", export_pdf.export_ventes_pdf, name="export_ventes_pdf"),
    path("graphs/", dash_ventes.dashboard_ventes, name="dashboard_ventes"),
    path("dashboard/pdf/", exp_pdf.dashboard_pdf, name="dashboard_pdf"),
    path(
        "revendeurs/invites",
        invites.inscriptions_par_revendeur,
        name="invites_revendeur",
    ),
    path(
        "conversation/<int:conversation_id>/conclure/",
        discussions.conclure_discussion,
        name="conclure_discussion",
    ),
]
