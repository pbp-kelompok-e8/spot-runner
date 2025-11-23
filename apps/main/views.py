from datetime import date
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User, Attendance, Runner
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from apps.event.models import Event, EventCategory
from apps.review.models import Review
from django.http import JsonResponse
from apps.main.forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.db import transaction

# Create your views here.

def show_main(request):
    """
    View untuk menampilkan halaman utama dengan daftar event.
    Mendukung filter berdasarkan kategori dari URL parameter.
    """
    # Ambil parameter filter dari URL
    current_category = request.GET.get('category', '')
    current_location = request.GET.get('location', '')
    current_status = request.GET.get('status', '')
    
    # Query semua event, urutkan berdasarkan event_date (descending)
    # Atau bisa pakai '-event_date' untuk event terdekat di atas
    events = Event.objects.all().order_by('event_date')
    
    # Filter berdasarkan kategori jika ada
    # Menggunakan event_category__category karena ini adalah ManyToMany
    if current_category:
        events = events.filter(event_category__category=current_category).distinct()
    
    # Filter berdasarkan lokasi jika ada
    if current_location:
        events = events.filter(location=current_location)
    
    # Filter berdasarkan status jika ada
    if current_status:
        events = events.filter(event_status=current_status)
    
    # Siapkan context untuk template
    context = {
        'events': events,
        'current_category': current_category,
        'current_location': current_location,
        'current_status': current_status,
    }
    
    return render(request, 'main.html', context)

def register(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():

            form.save()
            messages.success(request, "Akun berhasil dibuat! Silakan login.")
            return redirect('main:login')

        else:
            if 'email' in form.errors:
                messages.error(request, form.errors['email'][0]) # Pesan error dari form
            else:
                messages.error(request, "Pendaftaran gagal. Periksa kembali data yang kamu masukkan.")
            return redirect('main:register')

    context = {'form': form}
    return render(request, 'register.html', context)

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('main:show_main')

    else:
        form = AuthenticationForm(request)
    context = {'form': form}
    return render(request, 'login.html', context)

@login_required(login_url='main:login')
def show_user(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        messages.error(request, "You are not authorized to view this profile.")
        return redirect('main:show_main')
    
    if user.role != 'runner':
        context = {
            'user': user,
        }
        return render(request, "profile.html", context)

    attendance_list = user.runner.attendance_records.all().select_related('event').prefetch_related('event__event_category')
    today = date.today()
    
    reviews = Review.objects.filter(runner=user.runner).select_related('event')
    review_dict = {review.event_id: review for review in reviews}


    for record in attendance_list:
        event = record.event
        event_date = event.event_date.date()
        
        # Update status event
        if event_date < today:
            event.event_status = "finished"
        elif event_date == today:
            event.event_status = "on_going"
        else:
            event.event_status = "coming_soon"
        event.save()

        # Update status registrasi
        if event.event_status == "finished" and record.status == 'attending':
            record.status = 'finished'
            record.save()
        record.review = review_dict.get(event.id)

    context = {
        'user': user,
        'attendance_list': attendance_list,
        'location_choices': Runner.LOCATION_CHOICES,
        'user_reviews': reviews,
    }

    return render(request, "runner_detail.html", context)

def logout_user(request):
    username = request.user.username
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    messages.success(request, f'See u later, {username}!')
    response.delete_cookie('last_login')
    return response


@login_required(login_url='main:login')
def edit_profile_runner(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        return JsonResponse({"error": "You are not authorized to edit this profile."}, status=403)

    if request.method == 'POST':
        try:
            new_username = request.POST.get('username').strip()
            base_location = request.POST.get('base_location', '')

            if not new_username:
                return JsonResponse({"error": "Username cannot be empty"}, status=400)

            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exists():
                    return JsonResponse({"error": "Username already taken"}, status=400)
                user.username = new_username
                user.save()

            user.runner.base_location = base_location
            user.runner.save()
            
            new_urls = {
                "edit_profile": reverse('main:edit_profile', args=[user.username]),
                "change_password": reverse('main:change_password', args=[user.username]),
                "cancel_event_urls": {
                    str(record.event.id): reverse('main:cancel_event', args=[user.username, record.event.id])
                    for record in user.runner.attendance_records.filter(status='attending')
                }
            }

            return JsonResponse({
                    "success": True,
                    "username": user.username,
                    "base_location": user.runner.get_base_location_display(),
                    "message": "Profile updated successfully!",
                    "new_urls": new_urls 
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def cancel_event(request, username, id):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        print("You are not authorized to perform this action.")
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')
    
    event = get_object_or_404(Event, pk=id)
    runner = user.runner

    try:
        attendance = Attendance.objects.get(runner=runner, event=event)

        if attendance.status == 'attending':
            with transaction.atomic():
                attendance.status = 'canceled'
                attendance.save()
                
                event.decrement_participans() 
            
            print("You have successfully canceled your attendance for the event.")
            messages.success(request, f"You have successfully canceled your attendance for {event.name}.")
        
        elif attendance.status == 'canceled':
            print("You have already canceled this event.")
            messages.warning(request, "You have already canceled this event.")
        
        else:
            print("You cannot cancel an event that is already finished.")
            messages.error(request, "You cannot cancel an event that is already finished.")

    except Attendance.DoesNotExist:
        print("You are not registered for this event.")
        messages.error(request, "You are not registered for this event.")
    
    except Exception as e:
        print(f"An error occurred while canceling: {str(e)}")
        messages.error(request, f"An error occurred while canceling: {str(e)}")

    return redirect('main:show_user', username=username)


def participate_in_event(request, username, id, category_key):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')

    event = get_object_or_404(Event, pk=id)
    runner = user.runner

    try:

        selected_category = EventCategory.objects.get(
            category=category_key, 
            events=event
        )
    except EventCategory.DoesNotExist:
        messages.error(request, "Invalid category selected for this event.")
        return redirect('event:event_detail', pk=id)

    try:
        with transaction.atomic():
            if event.total_participans >= event.capacity:
                messages.error(request, f"Sorry, {event.name} is already full.")
                return redirect('main:show_user', username=username)

            attendance, created = Attendance.objects.get_or_create(
                runner=runner,
                event=event,
                defaults={
                        'status': 'attending',
                        'category': selected_category
                        }
                
            )

            if created:
                event.increment_participans()
                messages.success(request, f"You are now registered for {event.name}.")
            else:
                if attendance.status == 'canceled':
                    attendance.status = 'attending'
                    attendance.category = selected_category
                    attendance.save()
                    event.increment_participans() 
                    messages.success(request, f"You have re-registered for {event.name}.")
                else:
                    messages.warning(request, f"You are already registered for {event.name}.")
    
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect('main:show_user', username=username)

@login_required(login_url='main:login')
def change_password(request,username):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                return JsonResponse({"success": True})
            else:
                return JsonResponse({
                    "success": False,
                    "message": list(form.errors.values())[0][0]
                })

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated successfully!")
            return redirect('main:logout')
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = PasswordChangeForm(request.user)
    context = {
        'form':form,
        'user': request.user
    }

    return render(request, "change_password.html", context)

@login_required(login_url='main:login')
@require_POST
def delete_profile(request, username):
    user = request.user
    password = request.POST.get("password")

    if not user.check_password(password):
        return JsonResponse({
            "success": False,
            "message": "Password yang Anda masukkan salah."
        }, status=400)
    
    try:
        with transaction.atomic():
            if hasattr(user, 'runner'):
                active_attendances = Attendance.objects.filter(
                    runner=user.runner, 
                    status='attending'
                ).select_related('event')
                for attendance in active_attendances:
                    event = attendance.event
                    event.decrement_participans() 
            user.delete()
            logout(request)
        
        return JsonResponse({
            "success": True,
            "message": "Akun berhasil dihapus.",
            "redirect_url": reverse('main:show_main')
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Terjadi kesalahan: {str(e)}"
        }, status=500)