import asyncio
from locust import HttpUser, task, between

class ChatbotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def chat_with_bot(self):
        self.client.post(
            "/api/v1/chat",
            json={
                "message": "Recommend me a movie",
                "user_id": f"user_{self.user_id}"
            }
        ) 