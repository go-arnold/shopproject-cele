from django.views.decorators.csrf import csrf_exempt
import json
import tempfile
from weasyprint import HTML
from django.http import HttpResponse
from django.contrib.auth.models import Group
from django.templatetags.static import static
from django.core.exceptions import PermissionDenied


@csrf_exempt
def dashboard_pdf(request):
    user = request.user
    rev = Group.objects.get(name="revendeur").user_set.all()
    muk = Group.objects.get(name="mukubwa").user_set.all()
    if user in rev and user not in muk:
        raise PermissionDenied()
    if request.method == "POST":
        data = json.loads(request.body)
        images = data.get("images", [])
        logo_url = request.build_absolute_uri(static("static-img/logo-white.png"))

        html_content = f"""
        <html>
        <head>
           <style>
              @page {{
                   size: A4;
                   margin: 20mm;
                   background-color: #0d0817;
              }}
              body {{
                   font-family: Arial, sans-serif;
                   background: linear-gradient(135deg, #0d0817 0%, #1a0f2e 100%);
                   color: #e8e0f0;
                   text-align: center;
              }}
              .logo {{
                   width: 130px;
                   margin-bottom: 10px;
                   filter: drop-shadow(0 0 15px rgba(100, 13, 95, 0.6));
              }}

              h1 {{
                   text-align: center;
                   color: #d896d0;
                   margin-bottom: 40px;
                   font-size: 26px;
                   text-shadow: 0 0 20px rgba(100, 13, 95, 0.5);
              }}

              h2 {{
                   color: #c77dbf;
                   margin-top: 40px;
                   margin-bottom: 10px;
                   font-size: 20px;
                   text-shadow: 0 0 10px rgba(100, 13, 95, 0.3);
              }}

              .chart-container {{
                   margin-bottom: 40px;
                   text-align: center;
              }}

              img.chart {{
                   width: 100%;
                   border: 2px solid #640D5F;
                   border-radius: 8px;
                   box-shadow: 0 4px 20px rgba(100, 13, 95, 0.4);
                   /* background-color: white; pour éviter que le fond altère les images */
              }}
           </style>
        </head>
        <body>

            <img src="{logo_url}" class="logo" />
            <h1>Dashboard des Ventes</h1>
        """
        titles = [
            "Ventes des 7 derniers jours",
            "Chiffre d'affaires — 12 derniers mois",
            "Répartition des méthodes de paiement",
            "Top 10 des produits vendus",
            "Nombre de ventes par revendeur",
            "Chiffre d'affaires par revendeur",
            "Revenu habillement — 7 derniers jours",
        ]

        for index, img in enumerate(images):
            html_content += f"""
                <div class="chart-container">
                    <h2>{titles[index]}</h2>
                    <img class="chart" src="{img}" />
                </div>
            """

        html_content += """
        </body>
        </html>
        """

        html = HTML(string=html_content)

        with tempfile.NamedTemporaryFile(delete=True) as output_pdf:
            html.write_pdf(output_pdf.name)
            pdf_data = output_pdf.read()

        return HttpResponse(pdf_data, content_type="application/pdf")

    return HttpResponse(status=405)
