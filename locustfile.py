from locust import HttpUser, task, between

class UserBehavior(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # login once and store token. FastAPI OAuth2 expects Form Data!
        response = self.client.post("/auth/login", data={
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
                "/auth/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def login_burst(self):
        # This stresses the bcrypt hashing logic and needs the correct credentials!
        self.client.post("/auth/login", data={
            "username": "testuser@example.com",
            "password": "testuser"
        })
