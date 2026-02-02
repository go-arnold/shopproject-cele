import tempfile
from weasyprint import HTML

from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.models import Group
from django.templatetags.static import static
from django.core.exceptions import PermissionDenied
from django.db.models import F

from shop.models import Vente
from utils.decorators import admin_required


@admin_required
def export_ventes_pdf(request):
    user = request.user

    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()

    if user in rev and user not in muk:
        raise PermissionDenied()

    ventes_qs = (
        Vente.objects.select_related("produit", "utilisateur")
        .annotate(
            produit_nom_flat=F("produit__name"),
            produit_prix_flat=F("produit__price"),
            utilisateur_username_flat=F("utilisateur__username"),
        )
        .only(
            "date_achat",
            "method",
            "price_final",
            "produit__name",
            "produit__price",
            "utilisateur__username",
        )
        .order_by("-date_achat")
    )

    if not user.groups.filter(name="mukubwa").exists():
        ventes_qs = ventes_qs.filter(utilisateur=user)

    # ventes = ventes_qs[:1000]

    logo_url = request.build_absolute_uri(static("static-img/logo-white.png"))

    html_string = render_to_string(
        "gestion/pdf_ventes.html",
        {
            "ventes": ventes_qs,
            "logo_url": logo_url,
        },
    )

    html = HTML(string=html_string)

    with tempfile.NamedTemporaryFile(delete=True) as output:
        html.write_pdf(target=output.name)
        pdf_data = output.read()

    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="ventes.pdf"'
    return response
