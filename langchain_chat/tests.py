from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import LangChainThread, LangChainMessage
from .services import LangChainService, LangChainError

User = get_user_model()

class LangChainModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_create_thread(self):
        """Test creating a new thread"""
        thread = LangChainThread.objects.create(
            user=self.user,
            title="Test Thread",
            model_name="gpt-3.5-turbo"
        )
        self.assertEqual(thread.title, "Test Thread")
        self.assertEqual(thread.user, self.user)
        self.assertTrue(thread.is_active)

    def test_create_message(self):
        """Test creating a new message"""
        thread = LangChainThread.objects.create(
            user=self.user,
            title="Test Thread"
        )
        message = LangChainMessage.objects.create(
            user=self.user,
            thread=thread,
            content="Hello, AI!",
            role='user'
        )
        self.assertEqual(message.content, "Hello, AI!")
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.thread, thread)

class LangChainServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.service = LangChainService()

    def test_create_thread_service(self):
        """Test thread creation through service"""
        thread_data = self.service.create_thread(
            user_id=self.user.id,
            title="Service Test Thread"
        )
        self.assertIn('thread_id', thread_data)
        self.assertEqual(thread_data['title'], "Service Test Thread")

    @patch('langchain_chat.services.ChatOpenAI')
    @patch('langchain_chat.services.ConversationChain')
    def test_process_message(self, mock_chain, mock_chat):
        """Test message processing through service"""
        # Create a thread first
        thread_data = self.service.create_thread(
            user_id=self.user.id,
            title="Test Thread"
        )
        
        # Set up mock chain
        mock_instance = MagicMock()
        mock_instance.predict.return_value = "I am an AI assistant."
        mock_chain.return_value = mock_instance
        
        # Process a message
        response = self.service.process_message(
            thread_id=thread_data['thread_id'],
            user_id=self.user.id,
            content="Hello!"
        )
        
        self.assertIn('content', response)
        self.assertEqual(response['role'], 'assistant')
        self.assertEqual(response['content'], "I am an AI assistant.")
        mock_instance.predict.assert_called_once()

class LangChainAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a test thread
        self.thread = LangChainThread.objects.create(
            user=self.user,
            title="API Test Thread"
        )

    def test_list_threads(self):
        """Test retrieving thread list"""
        url = reverse('langchain-chat-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "API Test Thread")

    def test_create_thread(self):
        """Test creating a new thread via API"""
        url = reverse('langchain-chat-list')
        data = {
            'title': 'New Thread',
            'model_name': 'gpt-3.5-turbo'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Thread')

    def test_get_thread(self):
        """Test retrieving a specific thread"""
        url = reverse('langchain-chat-detail', args=[self.thread.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "API Test Thread")

    @patch('langchain_chat.services.ChatOpenAI')
    @patch('langchain_chat.services.ConversationChain')
    def test_send_message(self, mock_chain, mock_chat):
        """Test sending a message via API"""
        # Set up mock chain
        mock_instance = MagicMock()
        mock_instance.predict.return_value = "I am an AI assistant."
        mock_chain.return_value = mock_instance
        
        url = reverse('langchain-chat-message', args=[self.thread.id])
        data = {
            'content': 'Hello, AI!',
            'temperature': 0.7
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'assistant')
        self.assertEqual(response.data['content'], "I am an AI assistant.")
        mock_instance.predict.assert_called_once()

    def test_get_history(self):
        """Test retrieving chat history"""
        # Create some messages first
        LangChainMessage.objects.create(
            user=self.user,
            thread=self.thread,
            content="Hello!",
            role='user'
        )
        LangChainMessage.objects.create(
            user=self.user,
            thread=self.thread,
            content="Hi there!",
            role='assistant'
        )
        
        url = reverse('langchain-chat-history', args=[self.thread.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_thread(self):
        """Test deleting a thread"""
        url = reverse('langchain-chat-detail', args=[self.thread.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LangChainThread.objects.filter(id=self.thread.id).exists())

    def test_unauthorized_access(self):
        """Test unauthorized access to API endpoints"""
        self.client.force_authenticate(user=None)
        
        # Try to list threads
        url = reverse('langchain-chat-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to create a thread
        response = self.client.post(url, {'title': 'Unauthorized Thread'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
