import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app, get_db
from fastapi.testclient import TestClient

# Test DB URL
SQLALCHEMY_TEST_DATABASE_URL = "postgresql://gridfinity:development@localhost/gridfinity_test_db"

# Create test engine
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture(scope="session")
def setup_db():
    # Import all models to register them
    from app.models import User, Drawer, Bin, GeneratedFile, Baseplate

    # Drop and recreate all tables
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Print created tables
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = result.fetchall()
        print("\nCreated tables:", [table[0] for table in tables])

    yield test_engine

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    from app.models import User
    from app.utils.password import get_password_hash
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        hashed_password=get_password_hash("testpass123"),
        first_name="Test",
        last_name="User"
    )
    db_session.add(user)
    db_session.commit()
    return user