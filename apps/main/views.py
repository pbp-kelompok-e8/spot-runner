from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User
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
    return HttpResponse("Ini halaman main")

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
        pass
        # return render(request, "event_organizer_detail.html", context)
    context = {
        'user':user,
    }

    return render(request,"runner_detail.html",context)

def logout_user(request):
    username = request.user.username
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    messages.success(request, f'See u later, {username}!')
    response.delete_cookie('last_login')
    return response

def events_attended(request):
    user = get_object_or_404(User, username=request.username)
    event_list = user.attended_events.all()
    data = []
    for event in event_list:        
        category_names = [
            category.get_category_display() 
            for category in event.event_category.all()
        ]        
        data.append({
            'id': str(event.id),
            'name': event.name,
            'description': event.description,
            'location': event.get_location_display(), 
            'event_status' : event.status,
            'image': event.image,
            'image2': event.image2,
            'image3': event.image3,
            'event_date': event.event_date.isoformat(),
            'regist_deadline': event.regist_deadline.isoformat(),
            'contact': event.contact,
            'capacity': event.capacity,
            'total_participans': event.total_participans,
            'full': event.full,            
            'coin': event.coin, 
            'user_eo': {
                'id': event.user_eo_id,
                'username': event.user_eo.user.username if event.user_eo else None
                },            
            'event_categories': category_names 
        })
        
    return JsonResponse(data, safe=False)

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
        return redirect('event_organizer:profile')

    context = {
        'user': user,
    }
    return render(request, 'edit_profile.html', context)

