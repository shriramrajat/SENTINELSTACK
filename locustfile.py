import random
from locust import HttpUser, task, between

class UserBehavior(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000" # Dummy host to satisfy start requirement

    def on_start(self):
        # ⚖️ Permanent assignment of node per user session
        self.node = random.choice(["http://localhost:8000", "http://localhost:8001"])
        
        # login once and store token. FastAPI OAuth2 expects Form Data!
        response = self.client.post(f"{self.node}/auth/login", data={
            "username": "testuser@example.com",
            "password": "testuser"
        })

        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None

    @task(3)
    def get_profile(self):
        if self.token:
            self.client.get(
                f"{self.node}/auth/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def login_burst(self):
        # This stresses the bcrypt hashing logic and needs the correct credentials!
        self.client.post(f"{self.node}/auth/login", data={
            "username": "testuser@example.com",
            "password": "testuser"
        })
