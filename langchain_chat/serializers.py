from rest_framework import serializers
from .models import LangChainThread, LangChainMessage

class LangChainMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LangChainMessage
        fields = ['id', 'content', 'role', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']

class LangChainThreadSerializer(serializers.ModelSerializer):
    messages = LangChainMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = LangChainThread
        fields = ['id', 'title', 'is_active', 'created_at', 'updated_at', 
                 'model_name', 'metadata', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']

class MessageInputSerializer(serializers.Serializer):
    content = serializers.CharField(required=True)
    temperature = serializers.FloatField(required=False, default=0.7)
    metadata = serializers.JSONField(required=False, default=dict)

class ThreadCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    model_name = serializers.CharField(required=False, default="gpt-3.5-turbo")
    metadata = serializers.JSONField(required=False, default=dict) 