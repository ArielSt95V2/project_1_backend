from rest_framework import serializers
from .models import ChatHistory

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['id', 'message', 'timestamp', 'role']
        read_only_fields = ['id', 'timestamp', 'role']
