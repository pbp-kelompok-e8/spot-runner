from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from apps.main.models import User
from apps.main.forms import CustomUserCreationForm
from apps.main.forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import login, logout

# Create your views here.

def show_main(request):
    return HttpResponse("Ini halaman main")

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
        return render(request, "event_organizer_detail.html", context)
    context = {
        'user':user,
        'events': user.attended_events.all()
    }

    return render(request,"runner_detail.html",context)

def logout_user(request):
    username = request.user.username
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    messages.success(request, f'See u later, {username}!')
    response.delete_cookie('last_login')
    return response