from datetime import date
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User, Attendance, Runner
from apps.event.models import Event
from apps.review.models import Review
from django.http import JsonResponse
from apps.main.forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.db import transaction

# Create your views here.

def show_main(request):
    return render(request, 'main.html')

def register(request):
    form = CustomUserCreationForm()
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('main:login')
    context = {'form':form}
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

    attendance_list = user.runner.attendance_records.all().select_related('event')
    today = date.today()
    
    review_list = user.runner.reviews.all()

    # Update event statuses based on dates
    for record in attendance_list:
        event = record.event  # Ambil objek event dari record attendance
        
        # Cek jika event_date tidak None
        event_date = event.event_date.date()
        
        # Logika ini untuk mengubah status EVENT-nya
        if event_date < today:
            event.event_status = "finished"
        elif event_date == today:
            event.event_status = "on_going"
        else:
            event.event_status = "coming_soon"
        event.save() # Simpan perubahan status di OBJEK EVENT

        # Logika TAMBAHAN: Update status REGISTRASI-nya
        # Jika event-nya sudah selesai DAN status pendaftarannya 
        # masih 'attending', ubah jadi 'finished'.
        if event.event_status == "finished" and record.status == 'attending':
            record.status = 'finished'
            record.save() # Simpan perubahan status di OBJEK ATTENDANCE

    context = {
        'user': user,
        'attendance_list': attendance_list,  # Use the updated event_list
        'review_list': review_list
    }

    return render(request, "runner_detail.html", context)

def logout_user(request):
    username = request.user.username
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    messages.success(request, f'See u later, {username}!')
    response.delete_cookie('last_login')
    return response


@login_required
def edit_profile_runner(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to edit this profile.")
        return redirect('main:show_main')

    if request.method == 'POST':
        try:
            new_username = request.POST.get('username')
            base_location = request.POST.get('base_location', '')

            # Update username
            if new_username and new_username != request.user.username:
                if User.objects.filter(username=new_username).exists():
                    return JsonResponse({"error": "Username already taken"}, status=400)
                request.user.username = new_username
                request.user.save()

            # Update fields
            user.runner.base_location = base_location
            user.runner.save()

            return JsonResponse({
                    "success": True,
                    "username": user.username,
                    "base_location": user.runner.get_base_location_display(),
                    "message": "Profile updated successfully!"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

    context = {
        'user': user,
    }
    return render(request, 'edit_profile.html', context)

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
                
                # Panggil metode decrement dari model Event
                event.decrement_participans() 
            
            print("You have successfully canceled your attendance for the event.")
            messages.success(request, f"You have successfully canceled your attendance for {event.name}.")
        
        elif attendance.status == 'canceled':
            print("You have already canceled this event.")
            messages.warning(request, "You have already canceled this event.")
        
        else: # Statusnya adalah 'finished'
            print("You cannot cancel an event that is already finished.")
            messages.error(request, "You cannot cancel an event that is already finished.")

    except Attendance.DoesNotExist:
        print("You are not registered for this event.")
        messages.error(request, "You are not registered for this event.")
    
    # PERUBAHAN UTAMA: 
    # Tampilkan error yang sebenarnya jika terjadi kegagalan
    except Exception as e:
        print(f"An error occurred while canceling: {str(e)}")
        messages.error(request, f"An error occurred while canceling: {str(e)}")

    return redirect('main:show_user', username=username)


def participate_in_event(request, username, id):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')

    event = get_object_or_404(Event, pk=id)
    runner = user.runner

    # Gunakan transaction agar increment dan pembuatan attendance terjadi bersamaan
    try:
        with transaction.atomic():
            if event.full:
                messages.error(request, f"Sorry, {event.name} is already full.")
                return redirect('main:show_user', username=username)

            attendance, created = Attendance.objects.get_or_create(
                runner=runner,
                event=event,
                defaults={'status': 'attending'}
            )

            if created:
                # Jika baru dibuat, increment partisipan
                event.increment_participans()
                messages.success(request, f"You are now registered for {event.name}.")
            else:
                # Jika sudah ada, mungkin dia mendaftar ulang setelah cancel?
                if attendance.status == 'canceled':
                    attendance.status = 'attending'
                    attendance.save()
                    event.increment_participans() # Jangan lupa increment lagi
                    messages.success(request, f"You have re-registered for {event.name}.")
                else:
                    # Jika statusnya 'attending' atau 'finished', berarti sudah terdaftar
                    messages.warning(request, f"You are already registered for {event.name}.")
    
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect('main:show_user', username=username)

