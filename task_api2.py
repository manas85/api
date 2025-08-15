from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()

class User(BaseModel):
    username: str
    email: EmailStr
    password: str

# Use username as the key, and User as the value
user_db: dict[str, User] = {
    "sudhanshu": User(username="sudhanshu", email="abc@xyz.com", password="password123"),
    "amrender": User(username="amrender", email="adef@xyz.com", password="password456"),
    "mustafa": User(username="mustafa", email="ghi@xyz.com", password="password789"),
}

# @app.post("/register")
# def register(user: User):
#     if len(user.password) < 8:
#         return {"error": "Password must be at least 8 characters long."}
#     if user.username in user_db:
#         raise HTTPException(status_code=400, detail="Username already exists.")
#     user_db[user.username] = user
#     return {"message": f"User {user.username} registered successfully."}

@app.post("/add-username")
def add_username(user: User):
    if len(user.password) < 8:
        return {"error": "Password must be at least 8 characters long."}
    if user.username in user_db:
        raise HTTPException(status_code=400, detail="Username already exists.")
    user_db[user.username] = user
    return {"message": f"User {user.username} added successfully."}

@app.get("/users")
def get_all_users():
    return {username: user.dict() for username, user in user_db.items()}