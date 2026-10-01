import os
from locust import HttpUser, task, between, LoadTestShape
import time

class APIUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        token = os.environ.get("OIDC_TOKEN")
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        self.client.headers.update({"X-API-KEY": "secret-enterprise-key"})

    @task(3)
    def chat_query(self):
        payload = {
            "question": "What were our total expenses in Q3?",
            "conversation_id": "locust_session_1",
            "user_id": "locust_user_1"
        }
        self.client.post("/api/v1/chat/generate", json=payload)

    @task(2)
    def document_search(self):
        payload = {
            "query": "invoice",
            "limit": 5
        }
        self.client.post("/api/v1/chat/search", json=payload)

    @task(1)
    def health_check(self):
        self.client.get("/api/v1/health")

class StepLoadShape(LoadTestShape):
    """
    A step load shape
    Starts at 10 users, then steps to 25, 50, and 100 users.
    Each step lasts 60 seconds.
    """
    
    step_time = 60
    step_load = [10, 25, 50, 100]
    spawn_rate = 5
    
    def tick(self):
        run_time = self.get_run_time()
        
        step_index = int(run_time / self.step_time)
        
        if step_index < len(self.step_load):
            target_users = self.step_load[step_index]
            return (target_users, self.spawn_rate)
            
        return None # Stop test when all steps are complete

