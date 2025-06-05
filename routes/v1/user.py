import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status, Header, Depends, Response
from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash
from utils.db import get_db_connection

load_dotenv()

router = APIRouter()

# A Pydantic model for user input (includes password)
class User(BaseModel):
    id: int | None = None
    email: EmailStr
    name: str
    password: str

# A Pydantic model for user output (excludes password)
class UserOut(BaseModel):
    id: int | None = None
    email: EmailStr
    name: str

def verify_api_key(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    token = authorization[len("Bearer "):].strip()
    env_api_key = os.environ.get("API_KEY")
    if token != env_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return token

@router.get("/user", response_model=UserOut, dependencies=[Depends(verify_api_key)])
def get_user(email: EmailStr):
    """
    Retrieve a user by email without exposing the password hash.
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
    return UserOut(id=row["id"], email=row["email"], name=row["name"])

@router.put("/user", response_model=User, dependencies=[Depends(verify_api_key)])
def update_user(user: User):
    """
    Update an existing user or create a new user.
    The incoming plain-text password is hashed using Werkzeug.
    """
    hashed_password = generate_password_hash(user.password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user WHERE email = ?", (user.email,))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO user (email, name, password) VALUES (?, ?, ?)",
            (user.email, user.name, hashed_password),
        )
        user_id = cur.lastrowid
    else:
        cur.execute(
            "UPDATE user SET name = ?, password = ? WHERE email = ?",
            (user.name, hashed_password, user.email),
        )
        user_id = row["id"]
    conn.commit()
    conn.close()
    user.id = user_id
    user.password = hashed_password
    return user

@router.post("/user/new", response_model=User, dependencies=[Depends(verify_api_key)])
def new_user(user: User):
    """
    Create a new user.
    If the user already exists, an error is raised.
    The incoming plain-text password is hashed using Werkzeug.
    """
    hashed_password = generate_password_hash(user.password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user WHERE email = ?", (user.email,))
    if cur.fetchone() is not None:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    cur.execute(
        "INSERT INTO user (email, name, password) VALUES (?, ?, ?)",
        (user.email, user.name, hashed_password),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    user.id = user_id
    user.password = hashed_password
    return user

@router.delete("/user", response_model=UserOut, dependencies=[Depends(verify_api_key)])
def delete_user(email: EmailStr):
    """
    Delete a user by email.
    Returns the deleted user data without the password.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user WHERE email = ?", (email,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    cur.execute("DELETE FROM user WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return UserOut(id=row["id"], email=row["email"], name=row["name"])

@router.options("/user", dependencies=[Depends(verify_api_key)])
def options_user(response: Response):
    """
    Return allowed HTTP methods for the /user endpoint.
    """
    allowed_methods = ["GET", "PUT", "DELETE", "OPTIONS"]
    # Set Allow header and return the allowed_methods in the response body.
    response.headers["Allow"] = ", ".join(allowed_methods)
    return {"allowed_methods": allowed_methods}