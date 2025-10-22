from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def show_main(request):
    context = {
        
    }
    return render(request, "main.html",context)