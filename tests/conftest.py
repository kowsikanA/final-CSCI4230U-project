import pytest
from app import create_app
from extensions import db

@pytest.fixture()
def app():
    """Create a Flask app configured for in-memory database testing."""
    
    app = create_app()
    # Override the default config for tests
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # in-memory DB
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "test-secret"
    })

    # Create tables before each test
    with app.app_context():
        db.create_all()
        yield app  # This yields control to the test
        db.session.remove()
        db.drop_all()  # Clean up after test


@pytest.fixture()
def client(app):
    """Flask test client to simulate API requests."""
    return app.test_client()
