from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^', views.home),
    url(r'^/login/', views.perform_login),
    url(r'^/logout/', views.perform_logout),
]