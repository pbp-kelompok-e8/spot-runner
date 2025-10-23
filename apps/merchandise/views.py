from django.contrib.auth.decorators import login_required
from apps.merchandise.models import Redemption, Merchandise
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.db.models import Sum

# Merchandise landing page
def show_merchandise(request):
    user = request.user if request.user.is_authenticated else None
    context = {'user': user}
    is_organizer = False
    coin_balance = 0
    organizer_earned = 0
    

    # jika user punya Runner profile
    if hasattr(user, 'runner'):
        user = user.runner        # reverse OneToOne: User -> Runner
        coin_balance = user.coin

    # jika user juga punya EventOrganizer profile
    if hasattr(user, 'eventorganizer'):
        user = user.eventorganizer    # reverse OneToOne: User -> EventOrganizer
        # contoh: hitung total coins earned (atau properti lain)
        context['organizer_profile'] = user
        is_organizer = True
        earned = Redemption.objects.filter(merchandise__organizer=user).aggregate(total=Sum('total_coins'))['total']
        organizer_earned = earned or 0

    category = request.GET.get('category') or ''
    products = Merchandise.objects.all()

    if category:
        products = products.filter(category=category)

    context = {
        'user' : user,
        'products': products,
        'categories': Merchandise.CATEGORY_CHOICES,
        'selected_category': category,
        'is_organizer': is_organizer,
        'organizer_coins': organizer_earned,  
        'user_coins': coin_balance, 
    }
    return render(request, "merchandise_main.html", context)

def product_detail(request, pk):
    merchandise = get_object_or_404(Merchandise, pk=pk)
    # Check if current user is the organizer (to disable redeem)
    is_organizer = False
    is_organizer = request.user.is_authenticated and merchandise.organizer == request.user
    
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
    # """Add new merchandise product - Event Organizer only"""
    # # Check if user is event organizer
    # if not hasattr(request.user, 'role') or request.user.role != 'event_organizer':
    #     raise PermissionDenied("Only Event Organizers can add merchandise")
    
    # if request.method == 'POST':
    #     form = MerchandiseForm(request.POST)
    #     variant_formset = MerchVariantFormSet(request.POST)
    #     image_formset = MerchImageFormSet(request.POST, request.FILES)
        
    #     if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
    #         merchandise = form.save(commit=False)
    #         merchandise.organizer = request.user
    #         merchandise.save()
            
    #         # Save variants and images
    #         variant_formset.instance = merchandise
    #         variant_formset.save()
            
    #         image_formset.instance = merchandise
    #         image_formset.save()
            
    #         messages.success(request, 'Product added successfully!')
    #         return redirect('merchandise:show_merchandise')
    # else:
    #     form = MerchandiseForm()
    #     variant_formset = MerchVariantFormSet()
    #     image_formset = MerchImageFormSet()
    
    context = {
        # 'form': form,
        # 'variant_formset': variant_formset,
        # 'image_formset': image_formset,
        # 'title': 'Add New Product'
    }
    return render(request, "add_merchandise.html", context)


@login_required
def edit_merchandise(request, pk):
    # """Edit merchandise product - Owner only"""
    # merchandise = get_object_or_404(Merchandise, pk=pk)
    
    # # Check ownership
    # if merchandise.organizer != request.user:
    #     raise PermissionDenied("You can only edit your own products")
    
    # if request.method == 'POST':
    #     form = MerchandiseForm(request.POST, instance=merchandise)
    #     variant_formset = MerchVariantFormSet(request.POST, instance=merchandise)
    #     image_formset = MerchImageFormSet(request.POST, request.FILES, instance=merchandise)
        
    #     if form.is_valid() and variant_formset.is_valid() and image_formset.is_valid():
    #         form.save()
    #         variant_formset.save()
    #         image_formset.save()
            
    #         messages.success(request, 'Product updated successfully!')
    #         return redirect('merchandise:product_detail', pk=pk)
    # else:
    #     form = MerchandiseForm(instance=merchandise)
    #     variant_formset = MerchVariantFormSet(instance=merchandise)
    #     image_formset = MerchImageFormSet(instance=merchandise)
    
    context = {
        # 'form': form,
        # 'variant_formset': variant_formset,
        # 'image_formset': image_formset,
        # 'merchandise': merchandise,
        # 'title': 'Edit Product'
    }
    return render(request, "add_merchandise.html", context)


@login_required
@require_POST
def delete_merchandise(request, pk):
    # """Delete merchandise product - Owner only, AJAX endpoint"""
    # merchandise = get_object_or_404(Merchandise, pk=pk)
    
    # # Check ownership
    # if merchandise.organizer != request.user:
    #     return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    # merchandise.delete()
    return JsonResponse({'success': True})





# @login_required
# @require_POST
# def redeem_variant(request, variant_pk):
    # """Redeem merchandise variant - Regular users only, AJAX endpoint"""
    # variant = get_object_or_404(MerchVariant, pk=variant_pk)
    # merchandise = variant.merchandise
    
    # # Check if user is the organizer (disable redeem for own products)
    # if merchandise.organizer == request.user:
    #     return JsonResponse({'success': False, 'error': 'You cannot redeem your own products'}, status=400)
    
    # # Parse request data
    # try:
    #     data = json.loads(request.body)
    #     quantity = int(data.get('quantity', 1))
    # except (json.JSONDecodeError, ValueError):
    #     return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    # if quantity <= 0:
    #     return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    # total_price = merchandise.price_coins * quantity
    
    # # Check user coin balance
    # if not hasattr(request.user, 'runner'):
    #     return JsonResponse({'success': False, 'error': 'User profile not found'}, status=400)
    
    # user_coins = getattr(request.user.runner, 'coin', 0)
    # if user_coins < total_price:
    #     return JsonResponse({'success': False, 'error': 'Insufficient coins'}, status=400)
    
    # try:
    #     with transaction.atomic():
    #         # Lock variant for update to prevent race conditions
    #         variant = MerchVariant.objects.select_for_update().get(pk=variant_pk)
            
    #         # Check stock availability
    #         if variant.stock < quantity:
    #             return JsonResponse({'success': False, 'error': 'Insufficient stock'}, status=400)
            
    #         # Update stock
    #         variant.stock = F('stock') - quantity
    #         variant.save(update_fields=['stock'])
            
    #         # Update user coins
    #         request.user.runner.coin = F('coin') - total_price
    #         request.user.runner.save(update_fields=['coin'])
            
    #         # Update organizer coins (if they have a runner profile)
    #         if hasattr(merchandise.organizer, 'runner'):
    #             merchandise.organizer.runner.coin = F('coin') + total_price
    #             merchandise.organizer.runner.save(update_fields=['coin'])
            
    #         # Create redemption record
    #         redemption = Redemption.objects.create(
    #             user=request.user,
    #             merchandise=merchandise,
    #             variant=variant,
    #             price_per_item=merchandise.price_coins,
    #             quantity=quantity,
    #             total_coins=total_price
    #         )
            
    #         # Refresh to get updated values
    #         variant.refresh_from_db()
    #         request.user.runner.refresh_from_db()
            
    #         return JsonResponse({
    #             'success': True,
    #             'new_user_coins': request.user.runner.coin,
    #             'new_stock': variant.stock,
    #             'redemption_id': str(redemption.id)
    #         })
            
    # except Exception as e:
        # return JsonResponse({'success': False, 'error': str(e)}, status=500)
