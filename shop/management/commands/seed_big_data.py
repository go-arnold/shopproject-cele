import random
from decimal import Decimal
from io import BytesIO

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile

from faker import Faker
from PIL import Image
from reportlab.pdfgen import canvas

from shop.models import (
    Category, Product, Feature, Testimony, FavoriteProduct,
    Vente, Conversation, Message, Notification, Order, OrderItem
)

fake = Faker("fr_FR")
User = get_user_model()


# ------------------ HELPERS ------------------

def limit(value, max_len):
    if not value:
        return value
    return value[:max_len]


def generate_image_file(name="image.jpg", size=(300, 300)):
    file_obj = BytesIO()
    image = Image.new(
        "RGB",
        size,
        tuple(random.randint(0, 255) for _ in range(3))
    )
    image.save(file_obj, "JPEG")
    file_obj.seek(0)
    return ContentFile(file_obj.read(), name=name)


def generate_pdf_file(name="doc.pdf"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, fake.text(200))
    c.save()
    buffer.seek(0)
    return ContentFile(buffer.read(), name=name)


def valid_short_description():
    verbs = ["est", "offre", "permet", "dispose", "embarque", "intègre"]
    text = f"Ce produit {random.choice(verbs)} une excellente qualité et une bonne performance."
    return limit(text, 255)


def valid_long_description():
    sentences = [fake.sentence() for _ in range(random.randint(2, 5))]
    return " ".join(sentences)


# ------------------ COMMAND ------------------

class Command(BaseCommand):
    help = "Seed massive realistic data"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🌱 Seeding BIG data..."))

        revendeur_group = Group.objects.get(name="revendeur")
        mukubwa_group = Group.objects.get(name="mukubwa")

        # ---------------- USERS ----------------
        users = []
        for i in range(200):
            user = User.objects.create_user(
                username=limit(fake.user_name() + str(i), 150),
                email=limit(fake.email(), 254),
                password="password123"
            )
            users.append(user)

        for user in users:
            profile = user.profile

            profile.phone_number = limit(fake.unique.phone_number(), 20)
            profile.def_address = limit(fake.street_address(), 60)
            profile.def_country = limit(fake.country(), 60)
            profile.def_quarter_town = limit(fake.city(), 60)

            profile.deliv_address = limit(fake.street_address(), 60)
            profile.deliv_country = limit(fake.country(), 60)
            profile.deliv_quarter_town = limit(fake.city(), 60)

            profile.image.save(f"profile_{user.id}.jpg", generate_image_file(), save=False)

            if random.random() < 0.3:
                user.groups.add(revendeur_group)
            if random.random() < 0.05:
                user.groups.add(mukubwa_group)

            if random.random() < 0.5:
                profile.invited_by = random.choice(users)

            profile.code_revendeur = str(random.randint(1000, 9999))
            profile.save()

        # ---------------- CATEGORIES ----------------
        categories = []
        for _ in range(20):
            cat = Category.objects.create(
                name=limit(fake.unique.word().capitalize(), 100),
                description=fake.text(100)
            )
            cat.image.save(f"cat_{cat.id}.jpg", generate_image_file(), save=True)
            categories.append(cat)

        # ---------------- PRODUCTS ----------------
        products = []
        for _ in range(500):
            price = Decimal(random.randint(10, 500))

            product = Product.objects.create(
                name=limit(fake.word().capitalize() + " " + fake.word(), 255),
                description=valid_short_description(),
                long_description=valid_long_description(),
                price=price,
                price_primary=price + Decimal(random.randint(5, 50)),
                category_fk=random.choice(categories),
                rating=random.uniform(2, 5),
                reviews=random.randint(0, 500),
                chara_entretien="Laver à froid\nNe pas repasser\nSéchage doux",
                delivery_policy_phase1=fake.text(100),
                delivery_policy_phase2=fake.text(100),
            )

            for field in ["image", "image_one", "image_two", "image_three"]:
                getattr(product, field).save(
                    f"{field}_{product.id}.jpg",
                    generate_image_file(),
                    save=True
                )

            if random.random() < 0.4:
                product.price_solde = price - Decimal(random.randint(1, 5))
                product.save()

            for _ in range(random.randint(1, 5)):
                Feature.objects.create(
                    product=product,
                    name=limit(fake.word(), 100)
                )

            products.append(product)

        # ---------------- TESTIMONIES ----------------
        for _ in range(2000):
            Testimony.objects.create(
                product=random.choice(products),
                utilisateur=random.choice(users),
                rating=random.randint(1, 5),
                message=fake.text(300)
            )

        # ---------------- FAVORITES ----------------
        for _ in range(2000):
            try:
                FavoriteProduct.objects.create(
                    utilisateur=random.choice(users),
                    produit=random.choice(products)
                )
            except:
                pass

        # ---------------- SALES ----------------
        for _ in range(1500):
            Vente.objects.create(
                utilisateur=random.choice(users),
                produit=random.choice(products),
                price_final=Decimal(random.randint(10, 400)),
                method=random.choice(["OrangeMoney", "AirtelMoney", "M-Pesa", "Cash"]),
                vendu_a=limit(fake.name(), 50)
            )

        # ---------------- ORDERS ----------------
        orders = []
        revendeurs = User.objects.filter(groups__name="revendeur")

        for _ in range(500):
            user = random.choice(users)
            order = Order.objects.create(
                user=user,
                assigned_revendeur=random.choice(revendeurs) if revendeurs else None,
                total_price=Decimal(0),
                status=random.choice(["attente", "traitement", "terminé"])
            )

            total = Decimal(0)
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                qty = random.randint(1, 3)
                price = product.price

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    unit_price=price
                )
                total += price * qty

            order.total_price = total
            order.save()
            orders.append(order)

        # ---------------- CONVERSATIONS ----------------
        for _ in range(300):
            conv = Conversation.objects.create(
                is_from_cart=random.random() < 0.3,
                related_order=random.choice(orders) if random.random() < 0.3 else None
            )

            participants = random.sample(users, k=2)
            conv.participants.add(*participants)

            for _ in range(random.randint(1, 10)):
                msg = Message.objects.create(
                    conversation=conv,
                    sender=random.choice(participants),
                    content=fake.sentence(),
                    metadata={"auto": True}
                )
                if random.random() < 0.3:
                    msg.image.save(
                        f"msg_{msg.id}.jpg",
                        generate_image_file(size=(200, 200)),
                        save=True
                    )

        # ---------------- NOTIFICATIONS ----------------
        conversations = list(Conversation.objects.all())
        for _ in range(1000):
            Notification.objects.create(
                user=random.choice(users),
                conversation=random.choice(conversations),
                title=limit(fake.sentence(nb_words=6), 200),
                body=fake.text(100),
                type=random.choice(["order", "chat"]),
                is_read=random.choice([True, False]),
                is_order_assigned=random.choice([True, False]),
            )

        self.stdout.write(self.style.SUCCESS("✅ BIG DATA SEEDED SUCCESSFULLY"))
