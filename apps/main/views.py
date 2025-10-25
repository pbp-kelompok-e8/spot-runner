# apps/main/views.py
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User
from apps.event.models import Event  # Import model Event
from django.http import JsonResponse
from apps.main.forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout

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
    context = {
        'user':user,
        'event_list': user.runner.attended_events.all()
    }

    return render(request,"runner_detail.html",context)

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
        new_username = request.POST.get('username')
        base_location = request.POST.get('base_location', '')
        image_url = request.POST.get('profile_photo', '')

        # Update username
        if new_username and new_username != request.user.username:
            request.user.username = new_username
            request.user.save()

        # Update fields
        user.base_location = base_location
        if image_url:
            user.profile_picture = image_url
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('main:show_user', username=user.username)

    context = {
        'user': user,
    }
    return render(request, 'edit_profile.html', context)

def cancel_event(request, username, id):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')
    event = get_object_or_404(Event, pk=id)
    user.runner.attended_events.remove(event)
    messages.success(request, f"You have successfully canceled your attendance for {event.name}.")
    return redirect('main:show_user', username=username)

def participate_in_event(request, username, id):
    user = get_object_or_404(User, username=username)
    if user != request.user or user.role != 'runner':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('main:show_main')
    event = get_object_or_404(Event, pk=id)
    user.runner.attended_events.add(event)
    messages.success(request, f"You are now registered to attend {event.name}.")
    return redirect('main:show_user', username=username)