from rest_framework import serializers
from .models import ChatHistory, ChatThread

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id', 'message', 'timestamp', 'role', 'thread']
        read_only_fields = ['id', 'timestamp', 'role']

class ChatThreadSerializer(serializers.ModelSerializer):
    messages = ChatHistorySerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active', 'messages', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'message': last_message.message,
                'timestamp': last_message.timestamp,
                'role': last_message.role
            }
        return None
