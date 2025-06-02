from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash
from utils.db import get_db_connection

router = APIRouter()

# A Pydantic model for user input/output.
class User(BaseModel):
    id: int | None = None
    email: EmailStr
    name: str
    password: str

@router.get("/user", response_model=User)
def get_user(email: EmailStr):
    """
    Retrieve a user by email.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    # Return the user data. The password field here is stored as a hash.
    return User(id=row["id"], email=row["email"], name=row["name"], password=row["password"])

@router.post("/user", response_model=User)
def update_user(user: User):
    """
    Update an existing user or create a new user.
    The incoming plain-text password is hashed using Werkzeug.
    """
    # Hash the incoming password.
    hashed_password = generate_password_hash(user.password)
    conn = get_db_connection()
    cur = conn.cursor()
    # Check if the user exists (by email).
    cur.execute("SELECT * FROM user WHERE email = ?", (user.email,))
    row = cur.fetchone()
    if row is None:
        # Create new user.
        cur.execute(
            "INSERT INTO user (email, name, password) VALUES (?, ?, ?)",
            (user.email, user.name, hashed_password),
        )
        user_id = cur.lastrowid
    else:
        # Update existing user.
        cur.execute(
            "UPDATE user SET name = ?, password = ? WHERE email = ?",
            (user.name, hashed_password, user.email),
        )
        user_id = row["id"]
    conn.commit()
    conn.close()
    user.id = user_id
    user.password = hashed_password  # Return the stored hash.
    return user