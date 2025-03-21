from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import ChatThread, ChatHistory

User = get_user_model()

class ChatThreadTests(APITestCase):
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
        
        # Create test thread
        self.thread = ChatThread.objects.create(
            user=self.user,
            title='Test Thread'
        )

    def test_create_thread(self):
        """Test creating a new chat thread"""
        url = reverse('thread-list-create')
        data = {'title': 'New Test Thread'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatThread.objects.count(), 2)  # Original + new thread
        self.assertEqual(response.data['title'], 'New Test Thread')

    def test_list_threads(self):
        """Test listing all threads"""
        url = reverse('thread-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the test thread

    def test_get_thread_detail(self):
        """Test getting a specific thread"""
        url = reverse('thread-detail', kwargs={'pk': self.thread.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Thread')

    def test_update_thread(self):
        """Test updating a thread"""
        url = reverse('thread-detail', kwargs={'pk': self.thread.pk})
        data = {'title': 'Updated Thread Title'}
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Thread Title')

    def test_delete_thread(self):
        """Test soft deleting a thread"""
        url = reverse('thread-detail', kwargs={'pk': self.thread.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify thread is soft deleted
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_active)

class ChatMessageTests(APITestCase):
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
        
        # Create test thread
        self.thread = ChatThread.objects.create(
            user=self.user,
            title='Test Thread'
        )

    def test_send_message(self):
        """Test sending a message in a thread"""
        url = reverse('chat-message')
        data = {
            'thread_id': self.thread.id,
            'message': 'Hello, this is a test message'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ChatHistory.objects.count(), 2)  # User message + assistant response

    def test_get_thread_messages(self):
        """Test getting messages for a specific thread"""
        # First send a message
        send_url = reverse('chat-message')
        data = {
            'thread_id': self.thread.id,
            'message': 'Test message'
        }
        self.client.post(send_url, data, format='json')
        
        # Then get messages
        url = reverse('thread-messages', kwargs={'thread_id': self.thread.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_send_message_invalid_thread(self):
        """Test sending message to non-existent thread"""
        url = reverse('chat-message')
        data = {
            'thread_id': 99999,  # Non-existent thread ID
            'message': 'Test message'
        }
        
        response = self.client.post(url, data, format='json')
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
            title='Other Thread'
        )
        
        url = reverse('thread-messages', kwargs={'thread_id': other_thread.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
