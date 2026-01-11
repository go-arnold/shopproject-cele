from django.templatetags.static import static
from utils.email_custom import send_html_email
from django.shortcuts import redirect
from shop.models import Order, OrderItem, Conversation, Message, Notification
from django.contrib.auth.models import Group
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from utils.cart import Cart
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def start_conversation_from_cart(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect("all_products")

    order = Order.objects.create(
        user=request.user,
        total_price=cart.get_total_price(),
    )

    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            quantity=item["quantity"],
            unit_price=item["price"],
        )

    conversation = Conversation.objects.create(is_from_cart=True, related_order=order)
    conversation.participants.add(request.user)

    lines = []
    lines.append("Bonjour, je voudrais passer cette commande :\n")
    total = 0

    for item in cart:
        qty = item["quantity"]
        price = item["price"]
        name = item["product"].name
        subtotal = qty * price
        total += subtotal
        lines.append(f"- {name} × {qty} = {subtotal} $")
        item["line"] = f"{name} × {qty} = {subtotal} $"
        item["subtotal"] = subtotal

    lines.append(f"\nTotal : {total} $")

    auto_message = "\n".join(lines)

    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=auto_message,
        metadata={"generated_from_cart": True},
    )
    try:
        mukubwa_group = Group.objects.get(name="mukubwa")
        mukubwa_users = mukubwa_group.user_set.all()
    except Group.DoesNotExist:
        mukubwa_users = []

    recipients = []
    for admin in mukubwa_users:
        if admin.email:
            recipients.append(admin.email)
        Notification.objects.create(
            user=admin,
            title="Nouvelle commande",
            type="order",
            body=f"{request.user} a envoyé une demande d'achat.",
            conversation=conversation,
        )

    subject = "[ CELEBOBO-BUSINESS ] Nouvelle Commande Client"
    template_name = "shop/email_notify_mukubwa.html"
    text_content = f"{request.user} a envoyé une demande d'achat.\n\n\n {auto_message} \n\n Notification générée automatiquement par votre système"
    context = {
        "auto_message": auto_message,
        "logo_url": request.build_absolute_uri(static("static-img/logo-white.png")),
        "cart": cart,
        "total": total,
    }
    if isinstance(recipients, str):
        recipients = [recipients]
    try:
        send_html_email(subject, recipients, template_name, text_content, context)
        print("Email envoyé avec succès à:", recipients)
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

    cart.clear()

    return redirect("conversation_detail", conversation_id=conversation.id)


@login_required
def conversation_new(request):
    existing_convs = (
        Conversation.objects.filter(participants=request.user)
        .annotate(msg_count=Count("messages"))
        .filter(msg_count=0)
    )
    if existing_convs.exists():
        return redirect(
            "conversation_detail", conversation_id=existing_convs.first().id
        )

    conv = Conversation.objects.create(is_from_cart=False, related_order=None)

    return redirect("conversation_detail", conversation_id=conv.id)
