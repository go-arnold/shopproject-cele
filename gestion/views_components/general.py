from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncMonth, TruncDay
import json
from django.shortcuts import render
from django.db.models import Count, Sum
import tempfile
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse
import openpyxl
from django.utils import timezone
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from shop.models import Product, Feature, Category, Vente, Notification, Order, Conversation, Message
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from gestion.decorators import admin_required
from django.http import JsonResponse
from datetime import timedelta, datetime
from django.db.models import Sum, F, DecimalField
from django.utils.timezone import now
from django.db.models.functions import Coalesce
from django.templatetags.static import static
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
