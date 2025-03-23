from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import LangChainThread
from .serializers import (
    LangChainThreadSerializer,
    LangChainMessageSerializer,
    MessageInputSerializer,
    ThreadCreateSerializer
)
from .services import LangChainService, LangChainError

# Create your views here.

class LangChainChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.langchain_service = LangChainService()

    def list(self, request):
        """List all chat threads for the current user"""
        threads = LangChainThread.objects.filter(user=request.user)
        serializer = LangChainThreadSerializer(threads, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create a new chat thread"""
        serializer = ThreadCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                thread_data = self.langchain_service.create_thread(
                    user_id=request.user.id,
                    title=serializer.validated_data['title'],
                    model_name=serializer.validated_data.get('model_name', 'gpt-3.5-turbo')
                )
                thread = LangChainThread.objects.get(id=thread_data['thread_id'])
                response_serializer = LangChainThreadSerializer(thread)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except LangChainError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Get a specific chat thread and its messages"""
        thread = get_object_or_404(LangChainThread, id=pk, user=request.user)
        serializer = LangChainThreadSerializer(thread)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def message(self, request, pk=None):
        """Send a message in a specific chat thread"""
        thread = get_object_or_404(LangChainThread, id=pk, user=request.user)
        serializer = MessageInputSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                response = self.langchain_service.process_message(
                    thread_id=thread.id,
                    user_id=request.user.id,
                    content=serializer.validated_data['content'],
                    temperature=serializer.validated_data.get('temperature', 0.7)
                )
                return Response(response, status=status.HTTP_200_OK)
            except LangChainError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get the message history for a specific chat thread"""
        thread = get_object_or_404(LangChainThread, id=pk, user=request.user)
        try:
            messages = self.langchain_service.get_thread_history(thread.id)
            return Response(messages, status=status.HTTP_200_OK)
        except LangChainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, pk=None):
        """Delete a chat thread"""
        thread = get_object_or_404(LangChainThread, id=pk, user=request.user)
        try:
            self.langchain_service.delete_thread(thread.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except LangChainError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
