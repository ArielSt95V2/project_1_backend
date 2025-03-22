from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import ChatThread, ChatHistory
from .services import OpenAIAssistantService
from unittest.mock import patch, MagicMock

User = get_user_model()

class MockOpenAIResponse:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class ChatAPITestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Mock OpenAI responses
        self.mock_assistant = {
            'id': 'asst_123',
            'name': 'Test Assistant',
            'instructions': 'Test instructions',
            'model': 'gpt-4',
            'tools': [],
            'created_at': 1234567890
        }
        
        self.mock_thread = {'id': 'thread_123'}
        
        self.mock_message = {
            'id': 'msg_123',
            'role': 'assistant',
            'content': [{'text': {'value': 'Test response'}}]
        }

        # Create test thread
        self.thread = ChatThread.objects.create(
            user=self.user,
            title='Test Thread',
            openai_assistant_id='asst_123',
            openai_thread_id='thread_123'
        )

    @patch('chat.services.OpenAIAssistantService.list_assistants')
    def test_list_assistants(self, mock_list):
        """Test listing available assistants"""
        mock_list.return_value = [self.mock_assistant]
        
        response = self.client.get(reverse('assistant-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], 'asst_123')

    @patch('chat.services.OpenAIAssistantService.create_thread')
    def test_create_chat_thread(self, mock_create_thread):
        """Test creating a new chat thread"""
        mock_create_thread.return_value = self.mock_thread['id']
        
        data = {
            'title': 'Test Chat',
            'assistant_id': self.mock_assistant['id']
        }
        response = self.client.post(reverse('thread-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatThread.objects.count(), 2)  # Setup thread + new thread
        thread = ChatThread.objects.latest('created_at')
        self.assertEqual(thread.openai_thread_id, 'thread_123')
        self.assertEqual(thread.openai_assistant_id, 'asst_123')

    def test_list_threads(self):
        """Test listing all threads"""
        response = self.client.get(reverse('thread-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_thread_detail(self):
        """Test getting a specific thread"""
        response = self.client.get(reverse('thread-detail', kwargs={'pk': self.thread.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Thread')

    def test_update_thread(self):
        """Test updating a thread"""
        data = {'title': 'Updated Thread Title'}
        response = self.client.patch(
            reverse('thread-detail', kwargs={'pk': self.thread.pk}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Thread Title')

    def test_delete_thread(self):
        """Test soft deleting a thread"""
        response = self.client.delete(reverse('thread-detail', kwargs={'pk': self.thread.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify thread is soft deleted
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_active)

    @patch('chat.services.OpenAIAssistantService.add_message')
    @patch('chat.services.OpenAIAssistantService.run_assistant')
    def test_send_message(self, mock_run, mock_add):
        """Test sending a message in a thread"""
        mock_add.return_value = {'id': 'msg_123', 'role': 'user', 'content': 'Test message'}
        mock_run.return_value = {
            'run_id': 'run_123',
            'message': 'Test response'
        }
        
        data = {
            'thread_id': self.thread.id,
            'message': 'Test message'
        }
        response = self.client.post(reverse('message-create'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ChatHistory.objects.count(), 2)  # User message + Assistant response
        
        # Verify the messages
        messages = ChatHistory.objects.all().order_by('timestamp')
        self.assertEqual(messages[0].role, 'user')
        self.assertEqual(messages[0].message, 'Test message')
        self.assertEqual(messages[1].role, 'assistant')
        self.assertEqual(messages[1].message, 'Test response')

    def test_list_thread_messages(self):
        """Test listing messages in a thread"""
        # Create some test messages
        ChatHistory.objects.create(
            user=self.user,
            thread=self.thread,
            message='Hello',
            role='user'
        )
        ChatHistory.objects.create(
            user=self.user,
            thread=self.thread,
            message='Hi there!',
            role='assistant'
        )
        
        response = self.client.get(reverse('thread-messages', kwargs={'thread_id': self.thread.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['message'], 'Hello')
        self.assertEqual(response.data[1]['message'], 'Hi there!')

    def test_send_message_invalid_thread(self):
        """Test sending message to non-existent thread"""
        data = {
            'thread_id': 99999,  # Non-existent thread ID
            'message': 'Test message'
        }
        response = self.client.post(reverse('message-create'), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_messages_unauthorized_thread(self):
        """Test getting messages from another user's thread"""
        # Create another user and thread
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        other_thread = ChatThread.objects.create(
            user=other_user,
            title='Other Thread',
            openai_assistant_id='asst_456',
            openai_thread_id='thread_456'
        )
        
        response = self.client.get(reverse('thread-messages', kwargs={'thread_id': other_thread.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
