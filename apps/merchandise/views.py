from django.shortcuts import render
from django.http import HttpResponse
import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from .models import MerchVariant, Redemption, Merchandise

# Create your views here.

def show_merchandise(request):
    return render(request, "merchandise_main.html")

@login_required
def redeem_variant(request, variant_id):
    """
    POST endpoint. Body: {"quantity": 1}
    Returns JSON with redemption_id, remaining_coins, updated_stock
    """
    if request.method != 'POST':
        return JsonResponse({'status':'error', 'error':'Method not allowed'}, status=405)

    user = request.user
    body = json.loads(request.body.decode('utf-8') or '{}')
    qty = int(body.get('quantity', 1))
    if qty <= 0:
        return JsonResponse({'status':'error', 'error':'Invalid quantity'}, status=400)

    variant = get_object_or_404(MerchVariant, pk=variant_id)
    merchandise = variant.merchandise
    total_price = merchandise.price_coins * qty

    # Ensure user has coins field: user.coins (if you store coins in profile adjust accordingly)
    # If your coins are in profile, replace user.coins with user.profile.coins and lock profile.
    if not hasattr(user, 'coins'):
        return JsonResponse({'status':'error', 'error':'User coin balance not found.'}, status=500)

    try:
        with transaction.atomic():
            # Lock variant and user rows
            v = MerchVariant.objects.select_for_update().get(pk=variant.pk)
            u = type(user).objects.select_for_update().get(pk=user.pk)  # lock user row

            if not merchandise.is_active:
                return JsonResponse({'status':'error', 'error':'Product is not active.'}, status=400)
            if v.stock < qty:
                return JsonResponse({'status':'error', 'error':'Not enough stock.'}, status=400)
            if u.coins < total_price:
                return JsonResponse({'status':'error', 'error':'Not enough coins.'}, status=400)

            # decrement stock and coins atomically using F()
            v.stock = F('stock') - qty
            v.save(update_fields=['stock'])

            u.coins = F('coins') - total_price
            u.save(update_fields=['coins'])

            redemption = Redemption.objects.create(
                user=user,
                merchandise=merchandise,
                variant=v,
                price_per_item=merchandise.price_coins,
                quantity=qty,
                total_coins=total_price,
                status='redeemed'
            )

    except Exception as e:
        return JsonResponse({'status':'error', 'error': str(e)}, status=500)

    # refresh to read F() updated values
    v.refresh_from_db()
    u.refresh_from_db()

    return JsonResponse({
        'status': 'ok',
        'redemption_id': str(redemption.id),
        'remaining_coins': u.coins,
        'variant_stock': v.stock
    })

def merch_list(request):
    qs = Merchandise.objects.filter(is_active=True).select_related('organizer')
    category = request.GET.get('category')
    if category:
        qs = qs.filter(category=category)
    # pagination optional...
    context = {'products': qs, 'categories': Merchandise.CATEGORY_CHOICES}
    return render(request, 'merchandise/main.html', context)