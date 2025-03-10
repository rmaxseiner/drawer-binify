from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Removed password logging for security
        result = pwd_context.verify(plain_password, hashed_password)
        # Only log success/failure, not the actual password
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    try:
        # Removed password logging for security
        hashed = pwd_context.hash(password)
        # Only log masked hash for debugging
        print(f"Password hash generated successfully")
        return hashed
    except Exception as e:
        print(f"Error hashing password: {str(e)}")
        raise