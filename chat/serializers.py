from rest_framework import serializers
from .models import ChatHistory, ChatThread

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id', 'message', 'role', 'timestamp', 'openai_message_id']
        read_only_fields = ['id', 'timestamp']

class ChatThreadSerializer(serializers.ModelSerializer):
    messages = ChatHistorySerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ['id', 'title', 'is_active', 'created_at', 'updated_at', 
                 'openai_assistant_id', 'openai_thread_id', 'messages', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at', 'openai_thread_id']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return ChatHistorySerializer(last_message).data
        return None
