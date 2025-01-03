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

# OpenAI API call
openai_api_key = settings.OPENAI_API_KEY
client = OpenAI(api_key=openai_api_key)


class ChatHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatHistory.objects.filter(user=self.request.user).order_by('timestamp')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, role='user')  # Default role is 'user'


class ChatMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Save user message with role 'user'
        user_chat = ChatHistory.objects.create(user=request.user, message=user_message, role='user')

        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'user', 'content': user_message},
                ],
            )

            # Debug: Print the response to understand its structure
            print(response)

            # Access the assistant's message using attributes
            assistant_message = response.choices[0].message.content

            # Save assistant's reply with role 'assistant'
            assistant_chat = ChatHistory.objects.create(
                user=request.user, message=assistant_message, role='assistant'
            )

            # Return assistant's reply
            return Response({'message': assistant_message}, status=status.HTTP_200_OK)
        except Exception as e:
            # Print the exception for debugging
            print(f"Error during OpenAI API call: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







import string
from pathlib import Path
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from django.conf import settings

BASE_DIR = settings.BASE_DIR
# Dynamically set the path to nltk_data
# nltk.download('stopwords') nltk.download('punkt')
NLTK_DATA_DIR = Path(BASE_DIR) / 'nltk_data' 
nltk.data.path.append(str(NLTK_DATA_DIR))



class CleanTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Tokenize text
        tokens = word_tokenize(text)

        # Remove stop words and punctuation
        stop_words = set(stopwords.words('english'))
        cleaned_tokens = [word for word in tokens if word.lower() not in stop_words and word not in string.punctuation]

        # Join cleaned tokens into a cleaned text
        cleaned_text = ' '.join(cleaned_tokens)

        return Response({'cleaned_text': cleaned_text}, status=status.HTTP_200_OK)
