from django.urls import path
from .views import (
    ChatThreadListCreateView,
    ChatThreadDetailView,
    ChatMessageView,
    ThreadMessagesView,
    AssistantListView,
    AssistantDetailView
)

urlpatterns = [
    path('assistants/', AssistantListView.as_view(), name='assistant-list'),
    path('assistants/<str:assistant_id>/', AssistantDetailView.as_view(), name='assistant-detail'),
    path('threads/', ChatThreadListCreateView.as_view(), name='thread-list'),
    path('threads/<int:pk>/', ChatThreadDetailView.as_view(), name='thread-detail'),
    path('messages/', ChatMessageView.as_view(), name='message-create'),
    path('threads/<int:thread_id>/messages/', ThreadMessagesView.as_view(), name='thread-messages'),
]