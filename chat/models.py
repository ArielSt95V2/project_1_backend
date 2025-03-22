from django.db import models
from django.conf import settings

class ChatThread(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_threads'
    )
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # OpenAI specific fields
    openai_assistant_id = models.CharField(max_length=255, null=True, blank=True)
    openai_thread_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ChatHistory(models.Model):
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
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    timestamp = models.DateTimeField(auto_now_add=True)
    # OpenAI specific fields
    openai_message_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role} - {self.thread.title if self.thread else 'No Thread'}"
