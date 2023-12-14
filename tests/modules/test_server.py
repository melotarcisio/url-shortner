from fastapi.testclient import TestClient
from modules.models import UserCreate


def test_create_user(client: TestClient, some_user: UserCreate):
    client.post("/", json=some_user.dict())

    response = client.get("/")
    assert response.status_code == 200

    users = response.json()

    created = False
    for user in users:
        if user["username"] == some_user.username:
            created = True
            break

    assert created == True, "User was not created"
