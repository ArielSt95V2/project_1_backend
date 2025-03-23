from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LangChainChatViewSet

router = DefaultRouter()
router.register(r'threads', LangChainChatViewSet, basename='langchain-chat')

urlpatterns = [
    path('', include(router.urls)),
] 