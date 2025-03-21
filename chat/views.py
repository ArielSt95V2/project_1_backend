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

# OpenAI API call
openai_api_key = settings.OPENAI_API_KEY
client = OpenAI(api_key=openai_api_key)


class ChatThreadListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatThread.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        # Create OpenAI thread
        openai_thread = client.beta.threads.create()
        # Create our thread with OpenAI thread ID
        serializer.save(
            user=self.request.user,
            title=self.request.data.get('title', 'New Chat')
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
            
            # Save user message
            user_chat = ChatHistory.objects.create(
                user=request.user,
                thread=thread,
                message=message,
                role='user'
            )

            # Get thread history for context
            thread_messages = ChatHistory.objects.filter(thread=thread).order_by('timestamp')
            messages = [
                {'role': msg.role, 'content': msg.message}
                for msg in thread_messages
            ]

            # Get OpenAI response
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=messages,
            )

            assistant_message = response.choices[0].message.content

            # Save assistant's reply
            assistant_chat = ChatHistory.objects.create(
                user=request.user,
                thread=thread,
                message=assistant_message,
                role='assistant'
            )

            return Response({
                'message': assistant_message,
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
            # First check if the thread belongs to the user
            thread = ChatThread.objects.get(id=thread_id, user=self.request.user)
            return ChatHistory.objects.filter(
                thread=thread
            ).order_by('timestamp')
        except ChatThread.DoesNotExist:
            return ChatHistory.objects.none()  # Return empty queryset if thread not found

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

