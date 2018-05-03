from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def home(request):
    return render(request, 'index.html', context={'nav_bar': True})


@require_http_methods(["GET"])
@login_required
def perform_login(request):
    redirect = request.GET.get('next') or '/'
    return HttpResponseRedirect(redirect)


@require_http_methods(["GET"])
@login_required
def perform_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

