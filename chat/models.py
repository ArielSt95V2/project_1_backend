from django.db import models
from django.conf import settings

class ChatThread(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_threads'
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Thread {self.id} - {self.title or "Untitled"}'

    class Meta:
        ordering = ['-updated_at']

class ChatHistory(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_histories'
    )
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return f'[{self.role}] {self.user.email} at {self.timestamp}'

    class Meta:
        ordering = ['timestamp']
