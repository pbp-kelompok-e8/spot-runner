from django.contrib.auth.decorators import login_required
from apps.merchandise.models import Redemption, Merchandise
from apps.merchandise.forms import MerchandiseForm
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.db.models import Sum, F
from django.contrib import messages
import json

# test
# Merchandise landing page
def show_merchandise(request):
    # Initialize default values
    user = request.user
    is_organizer = False
    user_coins = 0
    organizer_coins = 0

    # Get products with optional category filtering
    category = request.GET.get('category', '')
    products = Merchandise.objects.all()
    if category:
        products = products.filter(category=category)

    # Check user role and get relevant data
    if user.is_authenticated:
        # Check if user is an Event Organizer
        # PENTING: Gunakan related_name yang sesuai dengan model
        # Jika model menggunakan related_name='event_organizer_profile'
        # maka gunakan: hasattr(user, 'event_organizer_profile')
        try:
            organizer_profile = user.event_organizer_profile
            is_organizer = True
            
            # Calculate total coins earned from merchandise redemptions
            earned = Redemption.objects.filter(
                merchandise__organizer=organizer_profile
            ).aggregate(
                total=Sum(F('quantity') * F('merchandise__price_coins'))
            )['total']
            organizer_coins = earned or 0
            
        except AttributeError:
            # User is not an organizer
            pass
        
        # Check if user is a Runner (to get their coin balance)
        try:
            runner_profile = user.runner
            user_coins = runner_profile.coin
        except AttributeError:
            # User is not a runner
            pass
    
    context = {
        'user': user,
        'products': products,
        'categories': Merchandise.CATEGORY_CHOICES,
        'selected_category': category,
        'is_organizer': is_organizer,
        'organizer_coins': organizer_coins,
        'user_coins': user_coins,
    }
    
    return render(request, "merchandise_main.html", context)

def product_detail(request, id):
    merchandise = get_object_or_404(Merchandise, id=id)
    
    is_organizer = False
    user_coins = 0
    
    if request.user.is_authenticated:
        # Check if current user is the organizer (to show edit/delete options)
        try:
            organizer_profile = request.user.event_organizer_profile
            is_organizer = merchandise.organizer == organizer_profile
        except AttributeError:
            pass
        
        # Get user coin balance for runners
        try:
            runner_profile = request.user.runner
            user_coins = runner_profile.coin
        except AttributeError:
            pass
    
    context = {
        'merchandise': merchandise,
        'is_organizer': is_organizer,
        'user_coins': user_coins,
    }
    return render(request, "product_detail.html", context)

@login_required(login_url='/login')
def add_merchandise(request):
    """Add new merchandise product - Event Organizer only"""
    # Check if user is event organizer
    try:
        organizer_profile = request.user.event_organizer_profile
    except AttributeError:
        messages.error(request, 'Only event organizers can add merchandise')
        return HttpResponseRedirect('/login')
    
    if request.method == 'POST':
        form = MerchandiseForm(request.POST)
        
        if form.is_valid():
            merchandise = form.save(commit=False)
            merchandise.organizer = organizer_profile
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


@login_required(login_url='/login')
def edit_merchandise(request, id):
    """Edit merchandise product - Owner only"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check ownership
    try:
        organizer_profile = request.user.event_organizer_profile
        if merchandise.organizer != organizer_profile:
            messages.error(request, 'You do not have permission to edit this product')
            return HttpResponseRedirect(reverse('merchandise:show_merchandise'))
    except AttributeError:
        messages.error(request, 'Only event organizers can edit merchandise')
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
    try:
        organizer_profile = request.user.event_organizer_profile
        if merchandise.organizer != organizer_profile:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    except AttributeError:
        return JsonResponse({'success': False, 'error': 'Only event organizers can delete merchandise'}, status=403)
    
    try:
        merchandise.delete()
        return JsonResponse({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def redeem_merchandise(request, id):
    """Redeem merchandise - Runner only, AJAX endpoint"""
    merchandise = get_object_or_404(Merchandise, id=id)
    
    # Check if user is a runner
    try:
        runner_profile = request.user.runner
    except AttributeError:
        return JsonResponse({'success': False, 'error': 'Only runners can redeem merchandise'}, status=403)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    # Validate quantity
    if quantity < 1:
        return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'}, status=400)
    
    if quantity > merchandise.stock:
        return JsonResponse({'success': False, 'error': f'Only {merchandise.stock} items in stock'}, status=400)
    
    # Check if user has enough coins
    total_cost = merchandise.price_coins * quantity
    if runner_profile.coin < total_cost:
        return JsonResponse({
            'success': False, 
            'error': f'Insufficient coins. Need {total_cost}, have {runner_profile.coin}'
        }, status=400)
    
    # Create redemption with explicit values
    redemption = Redemption.objects.create(
        user=runner_profile,
        merchandise=merchandise,
        quantity=quantity,
        price_per_item=merchandise.price_coins,
        total_coins=total_cost
    )
    
    # Update runner coins
    runner_profile.coin -= total_cost
    runner_profile.save()
    
    # Update organizer coins
    merchandise.organizer.coin += total_cost
    merchandise.organizer.save()
    
    # Update merchandise stock
    merchandise.stock -= quantity
    merchandise.save()
    
    return JsonResponse({
        'success': True, 
        'redemption_id': str(redemption.id),
        'total_coins': redemption.total_coins,
        'remaining_coins': runner_profile.coin
    })


@login_required
def history(request):
    """Show redemption history for runners and organizers"""
    user = request.user
    context = {}
    
    # Check if user is a runner
    try:
        runner_profile = user.runner
        redemptions = Redemption.objects.filter(user=runner_profile).order_by('-redeemed_at')
        context.update({
            'user_type': 'runner',
            'redemptions': redemptions,
            'user_coins': runner_profile.coin
        })
        return render(request, 'history.html', context)
    except AttributeError:
        pass
    
    # Check if user is an event organizer
    try:
        organizer_profile = user.event_organizer_profile
        redemptions = Redemption.objects.filter(
            merchandise__organizer=organizer_profile
        ).order_by('-redeemed_at')
        context.update({
            'user_type': 'organizer',
            'redemptions': redemptions,
            'organizer_coins': organizer_profile.coin
        })
        return render(request, 'history.html', context)
    except AttributeError:
        pass
    
    # User is neither runner nor organizer
    messages.error(request, 'Access denied')
    return HttpResponseRedirect('/login')
