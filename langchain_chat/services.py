from typing import Dict, Any, List, Optional
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import PromptTemplate
from .models import LangChainThread, LangChainMessage

class LangChainError(Exception):
    """Base exception for LangChain service errors"""
    pass

class ChainExecutionError(LangChainError):
    """Raised when chain execution fails"""
    pass

class MemoryError(LangChainError):
    """Raised when memory operations fail"""
    pass

class LangChainService:
    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        self.api_key = api_key
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""The following is a friendly conversation between a human and an AI. The AI is helpful, creative, clever, and very friendly.

Current conversation:
{history}
Human: {input}
AI:"""
        )

    def _create_llm(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7) -> ChatOpenAI:
        """Initialize the language model"""
        try:
            return ChatOpenAI(
                temperature=temperature,
                model_name=model_name,
                streaming=True,
                callbacks=[StreamingStdOutCallbackHandler()],
                openai_api_key=self.api_key
            )
        except Exception as e:
            raise ChainExecutionError(f"Failed to initialize LLM: {str(e)}")

    def _create_memory(self, memory_key: str = "history") -> ConversationBufferMemory:
        """Initialize conversation memory"""
        try:
            return ConversationBufferMemory(
                memory_key=memory_key,
                return_messages=True
            )
        except Exception as e:
            raise MemoryError(f"Failed to initialize memory: {str(e)}")

    def create_thread(self, user_id: int, title: str, model_name: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """Create a new conversation thread"""
        try:
            thread = LangChainThread.objects.create(
                user_id=user_id,
                title=title,
                model_name=model_name,
                langchain_memory_key=f"memory_{user_id}_{title}"
            )
            
            # Initialize system message
            LangChainMessage.objects.create(
                user_id=user_id,
                thread=thread,
                content="You are a helpful AI assistant.",
                role='system'
            )
            
            return {
                'thread_id': thread.id,
                'title': thread.title,
                'model_name': thread.model_name,
                'created_at': thread.created_at
            }
        except Exception as e:
            raise ChainExecutionError(f"Failed to create thread: {str(e)}")

    def process_message(
        self,
        thread_id: int,
        user_id: int,
        content: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Process a user message and generate a response"""
        try:
            thread = LangChainThread.objects.get(id=thread_id)
            
            # Save user message
            user_message = LangChainMessage.objects.create(
                user_id=user_id,
                thread=thread,
                content=content,
                role='user'
            )

            # Initialize LangChain components
            llm = self._create_llm(model_name=thread.model_name, temperature=temperature)
            memory = self._create_memory(memory_key="history")
            
            # Create conversation chain with custom prompt
            chain = ConversationChain(
                llm=llm,
                memory=memory,
                prompt=self.prompt,
                verbose=True
            )

            # Get conversation history
            history = LangChainMessage.objects.filter(
                thread=thread
            ).order_by('timestamp')

            # Load history into memory
            for msg in history:
                if msg.role != 'system':
                    memory.chat_memory.add_user_message(msg.content) if msg.role == 'user' \
                        else memory.chat_memory.add_ai_message(msg.content)

            # Generate response
            response = chain.predict(input=content)

            # Save assistant message
            assistant_message = LangChainMessage.objects.create(
                user_id=user_id,
                thread=thread,
                content=response,
                role='assistant'
            )

            return {
                'thread_id': thread.id,
                'message_id': assistant_message.id,
                'content': response,
                'role': 'assistant',
                'timestamp': assistant_message.timestamp
            }

        except LangChainThread.DoesNotExist:
            raise ChainExecutionError(f"Thread {thread_id} not found")
        except Exception as e:
            raise ChainExecutionError(f"Failed to process message: {str(e)}")

    def get_thread_history(self, thread_id: int) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a thread"""
        try:
            messages = LangChainMessage.objects.filter(
                thread_id=thread_id
            ).order_by('timestamp')
            
            return [
                {
                    'message_id': msg.id,
                    'content': msg.content,
                    'role': msg.role,
                    'timestamp': msg.timestamp,
                    'metadata': msg.metadata
                }
                for msg in messages
            ]
        except Exception as e:
            raise ChainExecutionError(f"Failed to retrieve thread history: {str(e)}")

    def delete_thread(self, thread_id: int) -> bool:
        """Delete a conversation thread and its messages"""
        try:
            thread = LangChainThread.objects.get(id=thread_id)
            thread.delete()
            return True
        except LangChainThread.DoesNotExist:
            raise ChainExecutionError(f"Thread {thread_id} not found")
        except Exception as e:
            raise ChainExecutionError(f"Failed to delete thread: {str(e)}") 