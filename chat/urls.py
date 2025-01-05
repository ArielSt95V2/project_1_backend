from django.urls import path
from .views import ChatHistoryListCreateView, ChatMessageView

urlpatterns = [
    path('history/', ChatHistoryListCreateView.as_view(), name='chat-history'),
    path('message/', ChatMessageView.as_view(), name='chat-message'),
]