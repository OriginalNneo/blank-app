from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from decouple import config
import pandas as pd

from app.services.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user against Google Sheets database"""
    try:
        db = get_db()
        users_df = db.get_users_df()

        if users_df.empty:
            print("No users found in database")
            return None

        # Clean whitespace and convert to lowercase for case-insensitive matching
        username = username.strip().lower()
        password = password.strip()

        # Convert username column to lowercase for comparison (handle NaN values)
        users_df['username_lower'] = users_df['username'].astype(str).str.strip().str.lower()
        
        # Filter for the specific user (case-insensitive)
        user_match = users_df[users_df['username_lower'] == username]

        if not user_match.empty:
            # Get stored password (handle NaN values)
            stored_password_raw = user_match.iloc[0]['password']
            if pd.isna(stored_password_raw):
                print(f"Password is NaN for user: {username}")
                return None
                
            stored_password = str(stored_password_raw).strip()
            
            if not stored_password:
                print(f"Password is empty for user: {username}")
                return None

            # Check password (support both hashed and plain text for migration)
            password_valid = False
            try:
                password_valid = verify_password(password, stored_password)
            except Exception as e:
                # If password verification fails (e.g., not a valid hash), try plain text comparison
                print(f"Password verification error for user {username}: {e}")
                password_valid = False

            # Try plain text comparison if bcrypt verification failed
            if not password_valid:
                password_valid = (stored_password == password)

            if password_valid:
                return {
                    "username": str(user_match.iloc[0]['username']).strip(),
                    "role": str(user_match.iloc[0].get('role', 'user')).strip(),
                    "email": str(user_match.iloc[0].get('email', '')).strip()
                }
            else:
                print(f"Password mismatch for user: {username}")
        else:
            print(f"User not found: {username}")
            print(f"Available usernames: {users_df['username'].astype(str).str.strip().tolist() if not users_df.empty else 'None'}")

    except Exception as e:
        print(f"Authentication error: {e}")
        import traceback
        traceback.print_exc()
        return None

    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None