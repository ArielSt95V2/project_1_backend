from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/', include('users.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/langchain/', include('langchain_chat.urls')),
]
