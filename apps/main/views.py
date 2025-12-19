from datetime import date
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User, Attendance, Runner
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, get_user_model
from apps.event.models import Event, EventCategory
from apps.review.models import Review
from apps.event_organizer.models import EventOrganizer
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
import requests
from django.views.decorators.csrf import csrf_exempt
import json
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
        
    if request.headers.get('Accept') == 'application/json' or '/json' in request.path:
            return JsonResponse({"status": "success", "message": "Event berhasil dibatalkan."})

    return redirect('main:show_user', username=username)

@csrf_exempt
@require_POST
def api_cancel_event(request, username, id):
    # 1. Validasi User
    if request.user.username != username:
        return JsonResponse({"status": "error", "message": "Unauthorized user"}, status=403)
    
    user = request.user
    if user.role != 'runner':
        return JsonResponse({"status": "error", "message": "Only runners can cancel events"}, status=403)

    # 2. Ambil Event & Runner
    event = get_object_or_404(Event, pk=id)
    runner = user.runner

    # 3. Logika Cancel
    try:
        attendance = Attendance.objects.get(runner=runner, event=event)

        if attendance.status == 'attending':
            with transaction.atomic():
                attendance.status = 'canceled'
                attendance.save()
                event.decrement_participans() 
            
            return JsonResponse({
                "status": "success", 
                "message": f"Successfully canceled attendance for {event.name}."
            }, status=200)
        
        elif attendance.status == 'canceled':
            return JsonResponse({
                "status": "warning", 
                "message": "You have already canceled this event."
            }, status=200)
        
        else:
            return JsonResponse({
                "status": "error", 
                "message": "Cannot cancel a finished event."
            }, status=400)

    except Attendance.DoesNotExist:
        return JsonResponse({
            "status": "error", 
            "message": "You are not registered for this event."
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            "status": "error", 
            "message": f"An error occurred: {str(e)}"
        }, status=500)


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

@csrf_exempt
@require_POST
def api_participate_event(request, username, id, category_key):
    # 1. Validasi User
    # Kita tidak perlu get_object_or_404 user karena request.user sudah ada
    if request.user.username != username:
        return JsonResponse({"status": "error", "message": "Unauthorized user"}, status=403)
    
    user = request.user
    if user.role != 'runner':
        return JsonResponse({"status": "error", "message": "Only runners can join events"}, status=403)

    # 2. Ambil Event & Kategori
    event = get_object_or_404(Event, pk=id)
    runner = user.runner

    try:
        selected_category = EventCategory.objects.get(
            category=category_key, 
            events=event
        )
    except EventCategory.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Invalid category"}, status=400)

    # 3. Logic Transaction (Sama persis)
    try:
        with transaction.atomic():
            if event.total_participans >= event.capacity:
                    return JsonResponse({"status": "error", "message": "Event is full"}, status=400)

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
                return JsonResponse({"status": "success", "message": f"Successfully joined {event.name}!"}, status=200)
            else:
                if attendance.status == 'canceled':
                    attendance.status = 'attending'
                    attendance.category = selected_category
                    attendance.save()
                    event.increment_participans() 
                    return JsonResponse({"status": "success", "message": f"Re-joined {event.name} successfully!"}, status=200)
                else:
                    return JsonResponse({"status": "warning", "message": "You are already registered."}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

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


@csrf_exempt
@require_POST
@login_required
def api_change_password(request):
    try:
        data = json.loads(request.body)
        user = request.user
        
        # PasswordChangeForm membutuhkan user dan data (dictionary)
        form = PasswordChangeForm(user, data)
        
        if form.is_valid():
            user = form.save()
            # Penting: update session agar user tidak ter-logout otomatis setelah ganti password
            update_session_auth_hash(request, user) 
            return JsonResponse({"status": "success", "message": "Password berhasil diubah!"}, status=200)
        else:
            # Ambil error pertama yang muncul
            first_error = list(form.errors.values())[0][0]
            return JsonResponse({"status": "error", "message": first_error}, status=400)
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

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

@csrf_exempt
@require_POST
@login_required
def api_delete_account(request):
    try:
        data = json.loads(request.body)
        password = data.get('password')
        user = request.user

        # 1. Validasi Password
        if not password:
                return JsonResponse({"status": "error", "message": "Password is required"}, status=400)

        if not user.check_password(password):
            return JsonResponse({"status": "error", "message": "Password salah."}, status=400)
        
        # 2. Hapus Data dengan Aman (Atomic)
        with transaction.atomic():
            # Jika user terdaftar di event, kurangi kuota partisipan event tersebut
            if hasattr(user, 'runner'):
                active_attendances = Attendance.objects.filter(
                    runner=user.runner, 
                    status='attending'
                ).select_related('event')
                
                for attendance in active_attendances:
                    event = attendance.event
                    event.decrement_participans() 
            
            # Hapus User
            user.delete()
            
            # Logout session (opsional tapi disarankan)
            logout(request)
            
        return JsonResponse({"status": "success", "message": "Akun berhasil dihapus."}, status=200)
        
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



def show_all_users_json(request):
    User = get_user_model()
    users = User.objects.all()  # Mengambil semua user dari database
    
    data_list = [] # List penampung

    for user in users:
        # Data dasar
        user_data = {
            "id": user.id, # Tambahkan ID agar lebih spesifik
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "details": None # Default null
        }

        # Cek Role dan Ambil Data Tambahan
        if user.role == 'runner':
            try:
                runner_profile = user.runner
                user_data["details"] = {
                    "base_location": runner_profile.base_location,
                    "coin": int(runner_profile.coin) if runner_profile.coin is not None else 0,
                }
            except Runner.DoesNotExist:
                pass # Biarkan details tetap None

        elif user.role == 'event_organizer':
            try:
                # Perhatikan related_name di model EventOrganizer
                eo_profile = user.event_organizer_profile 
                user_data["details"] = {
                    "base_location": eo_profile.base_location,
                    "profile_picture": eo_profile.profile_picture,
                    "total_events": eo_profile.total_events,
                    "rating": float(eo_profile.rating) if eo_profile.rating else 0.0,
                    "coin": int(eo_profile.coin) if eo_profile.coin is not None else 0,
                }
            except EventOrganizer.DoesNotExist:
                pass

        data_list.append(user_data)

    # safe=False wajib digunakan jika yang dikembalikan adalah List (bukan Dict)
    return JsonResponse(data_list, safe=False, status=200)

# views.py - api_profile
@csrf_exempt
@login_required
def api_profile(request):
    """API untuk mendapatkan data user profile (JSON)"""
    try:
        user = request.user
        
        # Build details based on user role
        details = {}
        
        if user.role == 'event_organizer':
            try:
                eo_profile = user.event_organizer_profile
                details = {
                    "base_location": eo_profile.base_location or "",
                    "profile_picture": eo_profile.profile_picture or "",
                    "total_events": Event.objects.filter(user_eo=eo_profile).count(),
                    "rating": float(eo_profile.rating) if eo_profile.rating else 0.0,
                    "coin": int(eo_profile.coin) if eo_profile.coin is not None else 0,
                }
            except (EventOrganizer.DoesNotExist, AttributeError):
                details = {
                    "base_location": "",
                    "profile_picture": "",
                    "total_events": 0,
                    "rating": 0.0,
                    "coin": 0,
                }
        elif user.role == 'runner':
            try:
                runner_profile = user.runner
                details = {
                    "base_location": runner_profile.base_location or "",
                    "coin": int(runner_profile.coin) if runner_profile.coin is not None else 0,
                }
            except (Runner.DoesNotExist, AttributeError):
                details = {
                    "base_location": "",
                    "coin": 0,
                }
        else:
            details = {
                "base_location": "",
                "coin": 0,
            }
        
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role or "user",
            "details": details
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=500)


# views.py - api_events
@csrf_exempt
@login_required
def api_events(request):
    """API untuk mendapatkan data events yang diorganisir user (JSON)"""
    try:
        user = request.user
        
        # Hanya event organizer yang memiliki events
        if user.role != 'event_organizer':
            return JsonResponse([], safe=False, status=200)
        
        # Dapatkan EventOrganizer profile
        try:
            eo_profile = user.event_organizer_profile
        except EventOrganizer.DoesNotExist:
            return JsonResponse([], safe=False, status=200)
        
        # Query events berdasarkan eo_profile (bukan user)
        events = Event.objects.filter(user_eo=eo_profile).order_by('-event_date')[:5]
        
        data = []
        for event in events:
            # Pastikan semua field ada
            event_status = getattr(event, 'event_status', 'On Going')
            
            # Format tanggal
            event_date = event.event_date
            if event_date:
                event_date_str = event_date.isoformat()
            else:
                event_date_str = "2024-12-04T00:00:00Z"
            
            regist_deadline = getattr(event, 'regist_deadline', None)
            if regist_deadline:
                regist_deadline_str = regist_deadline.isoformat()
            else:
                regist_deadline_str = event_date_str
            
            # Kategori event
            event_categories = []
            if hasattr(event, 'event_categories') and event.event_categories.exists():
                event_categories = list(event.event_categories.values_list('category', flat=True))
            
            event_obj = {
                "id": str(event.id),
                "name": event.name or "",
                "description": event.description or "",
                "location": event.location or "",
                "event_status": event_status,
                "image": event.image.url if hasattr(event.image, 'url') else "",
                "image2": None,
                "image3": None,
                "event_date": event_date_str,
                "regist_deadline": regist_deadline_str,
                "contact": event.contact or "",
                "capacity": event.capacity or 0,
                "total_participans": event.total_participans or 0,
                "full": event.full if hasattr(event, 'full') else False,
                "coin": event.coin or 0,
                "user_eo": {
                    "id": user.id,
                    "username": user.username
                },
                "event_categories": event_categories
            }
            
            data.append(event_obj)
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=500)

@login_required(login_url='main:login')
def show_user_json(request, username):
    user = get_object_or_404(User, username=username)

    # Validasi otorisasi
    if user != request.user:
        return JsonResponse({
            "status": "error",
            "message": "You are not authorized to view this profile."
        }, status=403)

    # Data dasar user
    user_data = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
        "status": "success", # Penting untuk pengecekan di Flutter
    }

    # Jika bukan runner, return basic info saja
    if user.role != 'runner':
        user_data["message"] = "User is not a runner"
        return JsonResponse(user_data, status=200)

    # Ambil profile runner
    try:
        runner_profile = user.runner
        user_data["base_location"] = runner_profile.base_location
        user_data["coin"] = runner_profile.coin
    except Runner.DoesNotExist:
            user_data["base_location"] = "-"
            user_data["coin"] = 0

    # Ambil Attendance List & Reviews
    attendance_list = runner_profile.attendance_records.all().select_related('event').prefetch_related('event__event_category')
    reviews = Review.objects.filter(runner=runner_profile).select_related('event')
    review_dict = {review.event_id: review for review in reviews}
    
    today = date.today()
    serialized_attendance = []
    
    for record in attendance_list:
        event = record.event
        event_date = event.event_date.date() if event.event_date else None
        
        # Update status event otomatis (sama seperti di HTML view)
        if event_date:
            is_changed = False
            if event_date < today and event.event_status != "finished":
                event.event_status = "finished"
                is_changed = True
            elif event_date == today and event.event_status != "on_going":
                event.event_status = "on_going"
                is_changed = True
            elif event_date > today and event.event_status != "coming_soon":
                event.event_status = "coming_soon"
                is_changed = True
            
            if is_changed:
                event.save()
                
        if event.event_status == "finished" and record.status == 'attending':
            record.status = 'finished'
            record.save()

        # Susun data attendance untuk JSON
        event_review = review_dict.get(event.id)
        serialized_attendance.append({
            "status": record.status,
            "category": record.category.category if record.category else "-",
            "participant_id": str(record.pk), # Atau field ID lain jika ada
            "event": {
                "id": str(event.id),
                "name": event.name,
                "location": event.location,
                "location_display": event.location, # Sesuaikan jika ada method get_display
                "event_date": event.event_date.strftime('%Y-%m-%d') if event.event_date else "-",
                "event_status": event.event_status,
            },
            "review": {
                "rating": event_review.rating,
                "review_text": event_review.review_text
            } if event_review else None
        })

    # Susun data Reviews untuk JSON
    serialized_reviews = []
    for r in reviews:
        serialized_reviews.append({
            "rating": r.rating,
            "review_text": r.review_text,
            "event": {
                "name": r.event.name,
            }
        })

    # Masukkan ke dictionary utama
    user_data["attendance_list"] = serialized_attendance
    user_data["user_reviews"] = serialized_reviews

    return JsonResponse(user_data, status=200)