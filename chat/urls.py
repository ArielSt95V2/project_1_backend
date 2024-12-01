from django.urls import path
from .views import ChatHistoryListCreateView, ChatMessageView, CleanTextView

urlpatterns = [
    path('history/', ChatHistoryListCreateView.as_view(), name='chat-history'),
    path('message/', ChatMessageView.as_view(), name='chat-message'),

    path('clean-text/', CleanTextView.as_view(), name='clean-text'),
]