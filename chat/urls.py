from django.urls import path
from .views import (
    ChatThreadListCreateView,
    ChatThreadDetailView,
    ChatMessageView,
    ThreadMessagesView
)

urlpatterns = [
    # Thread operations
    path('threads/', ChatThreadListCreateView.as_view(), name='thread-list-create'),
    path('threads/<int:pk>/', ChatThreadDetailView.as_view(), name='thread-detail'),
    
    # Message operations
    path('threads/<int:thread_id>/messages/', ThreadMessagesView.as_view(), name='thread-messages'),
    path('message/', ChatMessageView.as_view(), name='chat-message'),
]