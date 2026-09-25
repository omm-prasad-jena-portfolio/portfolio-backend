from django.urls import path
from .views import health_check, contact_view, chat_view

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('contact/', contact_view, name='contact'),
    path('chat/', chat_view, name='chat'),
]
