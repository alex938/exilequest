from django.urls import include, path

urlpatterns = [
    path("", include("quests.urls")),
]
