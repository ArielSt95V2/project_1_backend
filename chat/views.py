# chat/views.py

from rest_framework import generics, permissions, status
from .models import ChatHistory
from .serializers import ChatHistorySerializer

class ChatHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatHistory.objects.filter(user=self.request.user).order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# chat/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework import status, permissions
# from .models import ChatHistory
# from .serializers import ChatHistorySerializer
from django.conf import settings

from openai import OpenAI
from .models import ChatThread
from .serializers import ChatThreadSerializer
from .services import OpenAIAssistantService

# OpenAI API call
openai_api_key = settings.OPENAI_API_KEY
client = OpenAI(api_key=openai_api_key)

class AssistantListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            assistants = OpenAIAssistantService.list_assistants()
            return Response(assistants)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AssistantDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, assistant_id):
        try:
            assistant = OpenAIAssistantService.get_assistant(assistant_id)
            return Response(assistant)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatThreadListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatThread.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        assistant_id = self.request.data.get('assistant_id')
        if not assistant_id:
            return Response(
                {'error': 'Assistant ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create OpenAI thread
            openai_thread_id = OpenAIAssistantService.create_thread()
            
            # Create our thread with OpenAI IDs
            serializer.save(
                user=self.request.user,
                title=self.request.data.get('title', 'New Chat'),
                openai_assistant_id=assistant_id,
                openai_thread_id=openai_thread_id
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatThreadDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatThread.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class ChatMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        thread_id = request.data.get('thread_id')
        message = request.data.get('message')
        
        if not thread_id or not message:
            return Response(
                {'error': 'Thread ID and message are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the thread
            thread = ChatThread.objects.get(id=thread_id, user=request.user)
            
            # Add message to OpenAI thread
            openai_message = OpenAIAssistantService.add_message(
                thread.openai_thread_id,
                message,
                'user'
            )

            # Save user message locally
            user_chat = ChatHistory.objects.create(
                user=request.user,
                thread=thread,
                message=message,
                role='user',
                openai_message_id=openai_message['id']
            )

            # Run the assistant
            assistant_response = OpenAIAssistantService.run_assistant(
                thread.openai_thread_id,
                thread.openai_assistant_id
            )

            # Save assistant's reply locally
            assistant_chat = ChatHistory.objects.create(
                user=request.user,
                thread=thread,
                message=assistant_response['message'],
                role='assistant',
                openai_message_id=assistant_response['run_id']
            )

            return Response({
                'message': assistant_response['message'],
                'thread_id': thread_id
            }, status=status.HTTP_200_OK)

        except ChatThread.DoesNotExist:
            return Response(
                {'error': 'Thread not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ThreadMessagesView(generics.ListAPIView):
    serializer_class = ChatHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thread_id = self.kwargs.get('thread_id')
        try:
            thread = ChatThread.objects.get(id=thread_id, user=self.request.user)
            return ChatHistory.objects.filter(
                thread=thread
            ).order_by('timestamp')
        except ChatThread.DoesNotExist:
            return ChatHistory.objects.none()

    def list(self, request, *args, **kwargs):
        thread_id = self.kwargs.get('thread_id')
        try:
            ChatThread.objects.get(id=thread_id, user=request.user)
            return super().list(request, *args, **kwargs)
        except ChatThread.DoesNotExist:
            return Response(
                {'error': 'Thread not found or unauthorized.'},
                status=status.HTTP_404_NOT_FOUND
            )

