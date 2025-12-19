from django.urls import path
from .views import naplo_bevitel

urlpatterns = [
    path("bevitel/", naplo_bevitel, name="naplo_bevitel"),
    path("bevitel/<int:pk>/", naplo_bevitel, name="naplo_bevitel_edit"),
]
