from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User
from app.utils.password import get_password_hash  # Change this line

# Database connection URL
SQLALCHEMY_DATABASE_URL = "postgresql://gridfinity:development@localhost/gridfinity_db"

# Create database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create all tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a new database session
db = SessionLocal()

try:
    # Create test user
    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        first_name="Test",
        last_name="User"
    )

    # Add user to session and commit
    db.add(test_user)
    db.commit()
    print("Test user created successfully!")
    print("Username: testuser")
    print("Password: testpass123")

except Exception as e:
    print(f"Error creating test user: {e}")
    db.rollback()
finally:
    db.close()