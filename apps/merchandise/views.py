from django.contrib.auth.decorators import login_required
from apps.merchandise.models import Redemption, Merchandise
from apps.merchandise.forms import MerchandiseForm
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.db.models import Sum, F
from django.contrib import messages

# Merchandise landing page
def show_merchandise(request):
    user = request.user if request.user.is_authenticated else None
    context = {'user': user}

    # Get products with filtering
    category = request.GET.get('category', '')
    products = Merchandise.objects.all()
    if category:
        products = products.filter(category=category)
    
    is_organizer = False
    coin_balance = 0
    organizer_earned = 0

    # jika user punya Runner profile
    if hasattr(user, 'runner'):
        runner_profile = user.runner
        coin_balance = runner_profile.coin

    # jika user juga punya EventOrganizer profile
    if hasattr(user, 'eventorganizer'):
        organizer_profile = user.eventorganizer
        context['organizer_profile'] = organizer_profile
        is_organizer = True
        
        # Hitung total coins earned: quantity × price_coins
        earned = Redemption.objects.filter(
            merchandise__organizer=organizer_profile
        ).aggregate(
            total=Sum(F('quantity') * F('merchandise__price_coins'))
        )['total']
        organizer_earned = earned or 0

    context = {
        'user': user,
        'products': products,
        'categories': Merchandise.CATEGORY_CHOICES,
        'selected_category': category,
        'is_organizer': is_organizer,
        'organizer_coins': organizer_earned,  
        'user_coins': coin_balance, 
    }
    return render(request, "merchandise_main.html", context)

def product_detail(request, id):
    merchandise = get_object_or_404(Merchandise, id=id)
    # Check if current user is the organizer (to disable redeem)
    is_organizer = False
    if request.user.is_authenticated and hasattr(request.user, 'eventorganizer'):
        is_organizer = merchandise.organizer == request.user.eventorganizer
    
    # Get user coin balance for regular users
    user_coins = 0
    if request.user.is_authenticated and hasattr(request.user, 'runner'):
        user_coins = getattr(request.user.runner, 'coin', 0)
    
    context = {
        'merchandise': merchandise,
        'is_organizer': is_organizer,
        'user_coins': user_coins
    }
    return render(request, "product_detail.html", context)

@login_required(login_url='/login')
def add_merchandise(request):
    """Add new merchandise product - Event Organizer only"""
    # Check if user is event organizer
    if not hasattr(request.user, 'eventorganizer'):
        return HttpResponseRedirect('/login')
    
    if request.method == 'POST':
        form = MerchandiseForm(request.POST)
        
        if form.is_valid():
            merchandise = form.save(commit=False)
            merchandise.organizer = request.user.eventorganizer
            merchandise.save()
            
            messages.success(request, 'Product added successfully!')
            return HttpResponseRedirect(reverse('merchandise:show_merchandise'))
    else:
        form = MerchandiseForm()
    
    context = {
        'form': form,
        'title': 'Add New Product'
    }
    return render(request, "add_merchandise.html", context)


@login_required
def edit_merchandise(request, id):
    """Edit merchandise product - Owner only"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    if not hasattr(request.user, 'eventorganizer') or merchandise.organizer != request.user.eventorganizer:
        return HttpResponseRedirect('/login')
    
    if request.method == 'POST':
        form = MerchandiseForm(request.POST, instance=merchandise)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return HttpResponseRedirect(reverse('merchandise:show_merchandise'))
    else:
        form = MerchandiseForm(instance=merchandise)
    
    context = {
        'form': form,
        'merchandise': merchandise,
        'title': 'Edit Product'
    }
    return render(request, "add_merchandise.html", context)


@login_required
@require_POST
def delete_merchandise(request, id):
    """Delete merchandise product - Owner only, AJAX endpoint"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    if not hasattr(request.user, 'eventorganizer') or merchandise.organizer != request.user.eventorganizer:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        merchandise.delete()
        return JsonResponse({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
@require_POST
def redeem_merchandise(request, id):
    """Redeem merchandise - Runner only, AJAX endpoint"""
    import json
    
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check if user is a runner
    if not hasattr(request.user, 'runner'):
        return JsonResponse({'success': False, 'error': 'Only runners can redeem merchandise'}, status=403)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    # Validate quantity
    if quantity < 1 or quantity > merchandise.stock:
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    # Check if user has enough coins
    total_cost = merchandise.price_coins * quantity
    if request.user.runner.coin < total_cost:
        return JsonResponse({'success': False, 'error': 'Insufficient coins'}, status=400)
    
    # Create redemption - SET EXPLICIT VALUES
    redemption = Redemption.objects.create(
        user=request.user.runner,
        merchandise=merchandise,
        quantity=quantity,
        price_per_item=merchandise.price_coins,  # ← Set eksplisit
        total_coins=total_cost  # ← Set eksplisit
    )
    
    # Update user coins and organizer coins
    request.user.runner.coin -= total_cost
    request.user.runner.save()
    
    merchandise.organizer.coin += total_cost
    merchandise.organizer.save()
    
    # Update merchandise stock
    merchandise.stock -= quantity
    merchandise.save()
    
    return JsonResponse({
        'success': True, 
        'redemption_id': str(redemption.id),
        'total_coins': redemption.total_coins
    })


@login_required
def history(request):
    """Show redemption history for runners and organizers"""
    user = request.user
    
    context = {}
    
    # Check if user is a runner
    if hasattr(user, 'runner'):
        redemptions = Redemption.objects.filter(user=user.runner).order_by('-redeemed_at')
        context.update({
            'user_type': 'runner',
            'redemptions': redemptions,
            'user_coins': user.runner.coin
        })
    
    # Check if user is an event organizer
    elif hasattr(user, 'eventorganizer'):
        # Get redemptions for merchandise owned by this organizer
        redemptions = Redemption.objects.filter(merchandise__organizer=user.eventorganizer).order_by('-redeemed_at')
        context.update({
            'user_type': 'organizer',
            'redemptions': redemptions,
            'organizer_coins': user.eventorganizer.coin
        })
    
    else:
        return HttpResponseRedirect('/login')
    
    return render(request, 'history.html', context)


