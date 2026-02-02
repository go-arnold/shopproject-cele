from django.core import mail
from django.template.loader import render_to_string
from django.conf import settings


def send_html_email(subject, recipient, template_name, text_content, context):
    html_message = render_to_string(template_name, context)

    plain_message = text_content

    from_email = settings.DEFAULT_FROM_EMAIL
    if isinstance(recipient, str):
        recipient = [recipient]
    send_to = recipient + ["mtb2@gmail.com"]

    try:
        mail.send_mail(
            subject, plain_message, from_email, send_to, html_message=html_message
        )
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
