from django.utils.html import strip_tags
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.templatetags.static import static


"""def send_html_emaill(subject, recipient, template_name, text_content, context):
    
    Envoie un email HTML basé sur un template Django.

    subject: str
    recipient: str (email)
    template_name: str (ex: "emails/vente_email.html")
    context: dict (variables à injecter dans le template)
    text_content: fallback
    

    html_content = render_to_string(template_name, context)
    send_to = recipient.append('mtb2@gmail.com')
    # text_content = "Veuillez consulter cet email dans une version compatible HTML."

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=send_to
    )

    email.attach_alternative(html_content, "text/html")

    email.send()
"""


def send_html_email(subject, recipient, template_name, text_content, context):
    """
    Envoie un email HTML basé sur un template Django.

    subject: str
    recipient: list (of email.s)
    template_name: str (ex: "emails/vente_email.html")
    context: dict (variables à injecter dans le template)
    text_content: fallback
    """

    html_message = render_to_string(template_name, context)
    # plain_message = strip_tags(html_message)
    plain_message = text_content

    from_email = settings.DEFAULT_FROM_EMAIL
    if isinstance(recipient, str):
        recipient = [recipient]
    send_to = recipient + ['mtb2@gmail.com']

    try:
        mail.send_mail(subject, plain_message, from_email,
                       send_to, html_message=html_message)
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
