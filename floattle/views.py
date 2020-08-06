from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.views import generic
from .forms import LoginForm

# Create your views here.
def index(request):
    return HttpResponse('Hello, This is top page.')

class Top(generic.TemplateView):
    template_name = 'floattle/top.html'

class Login(LoginView):
    form_class = LoginForm
    template_name = 'floattle/login.html'

class Logout(LogoutView):
    template_name = 'floattle/top.html'
