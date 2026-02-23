from django.urls import path
from . import views

urlpatterns = [
    path("", views.quest_list, name="quest_list"),
    path("healthz/", views.healthz, name="healthz"),
]
