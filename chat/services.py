from openai import OpenAI
from django.conf import settings
from typing import List, Dict, Any, Optional

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class OpenAIAssistantService:
    @staticmethod
    def list_assistants() -> List[Dict[str, Any]]:
        """List all available assistants from OpenAI"""
        try:
            assistants = client.beta.assistants.list()
            return [
                {
                    'id': assistant.id,
                    'name': assistant.name,
                    'instructions': assistant.instructions,
                    'model': assistant.model,
                    'tools': assistant.tools,
                    'created_at': assistant.created_at
                }
                for assistant in assistants.data
            ]
        except Exception as e:
            raise Exception(f"Failed to fetch assistants: {str(e)}")

    @staticmethod
    def get_assistant(assistant_id: str) -> Dict[str, Any]:
        """Get a specific assistant by ID"""
        try:
            assistant = client.beta.assistants.retrieve(assistant_id)
            return {
                'id': assistant.id,
                'name': assistant.name,
                'instructions': assistant.instructions,
                'model': assistant.model,
                'tools': assistant.tools,
                'created_at': assistant.created_at
            }
        except Exception as e:
            raise Exception(f"Failed to fetch assistant: {str(e)}")

    @staticmethod
    def create_thread() -> str:
        """Create a new thread"""
        try:
            thread = client.beta.threads.create()
            return thread.id
        except Exception as e:
            raise Exception(f"Failed to create thread: {str(e)}")

    @staticmethod
    def add_message(thread_id: str, content: str, role: str = "user") -> Dict[str, Any]:
        """Add a message to a thread"""
        try:
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content
            )
            return {
                'id': message.id,
                'role': message.role,
                'content': message.content[0].text.value
            }
        except Exception as e:
            raise Exception(f"Failed to add message: {str(e)}")

    @staticmethod
    def run_assistant(thread_id: str, assistant_id: str) -> Dict[str, Any]:
        """Run the assistant on a thread"""
        try:
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            # Wait for the run to complete
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    raise Exception("Assistant run failed")
                elif run_status.status == 'expired':
                    raise Exception("Assistant run expired")
                elif run_status.status == 'cancelled':
                    raise Exception("Assistant run cancelled")
                
            # Get the assistant's response
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            assistant_message = next(
                (msg for msg in messages.data if msg.role == "assistant"),
                None
            )
            
            if not assistant_message:
                raise Exception("No assistant response found")
                
            return {
                'run_id': run.id,
                'message': assistant_message.content[0].text.value
            }
        except Exception as e:
            raise Exception(f"Failed to run assistant: {str(e)}")

    @staticmethod
    def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a thread"""
        try:
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            return [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content[0].text.value,
                    'created_at': msg.created_at
                }
                for msg in messages.data
            ]
        except Exception as e:
            raise Exception(f"Failed to fetch thread messages: {str(e)}") 