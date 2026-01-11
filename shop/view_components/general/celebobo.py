from datetime import datetime
from django.utils import timezone
from django.shortcuts import render


def aboutUs(request):
    """Rend la page 'À propos'."""
    return render(request, "shop/about.html")


def assistant(request):
    now = timezone.now()

    target = timezone.make_aware(datetime(now.year, 1, 18))
    if now > target:
        target = timezone.make_aware(datetime(now.year + 1, 1, 18))

    remaining = target - now

    days = remaining.days
    seconds = remaining.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return render(
        request,
        "shop/assistant.html",
        {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": secs,
        },
    )


def messages(request):
    html_to_render2 = "shop/login_required.html"

    if not request.user.is_authenticated:
        return render(request, html_to_render2)
    return render(request, "shop/conversations.html")
