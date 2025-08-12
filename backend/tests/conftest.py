import pytest
import redis
import os
from unittest.mock import Mock, MagicMock, patch
from app.BloomFilter import BloomFilter
from fastapi.testclient import TestClient

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ.update({
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "",
        "REDIS_SSL": "false",
        "BLOOM_EXPECTED_ITEMS": "1000",
        "BLOOM_FALSE_POSITIVE_RATE": "0.01",
        "BLOOM_REDIS_KEY": "bloom:passwords:test",
    })

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    from app.config import Settings
    
    # Use environment variables to set test values
    test_env = {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "",
        "REDIS_SSL": "false",
        "BLOOM_EXPECTED_ITEMS": "1000",
        "BLOOM_FALSE_POSITIVE_RATE": "0.01",
        "BLOOM_REDIS_KEY": "bloom:passwords:test"
    }
    
    with patch.dict(os.environ, test_env):
        settings = Settings()
        with patch('app.config.settings', settings):
            with patch('app.main.settings', settings):
                yield settings

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.setbit.return_value = 0
    mock_client.getbit.return_value = 1
    mock_client.bitcount.return_value = 100
    mock_client.close.return_value = None
    
    # Mock pipeline properly
    mock_pipeline = Mock()
    mock_pipeline.setbit.return_value = None
    mock_pipeline.getbit.return_value = None
    mock_pipeline.execute.return_value = [1, 1, 1, 1, 1]  # All bits set for testing
    mock_pipeline.__enter__ = Mock(return_value=mock_pipeline)
    mock_pipeline.__exit__ = Mock(return_value=None)
    
    mock_client.pipeline.return_value = mock_pipeline
    return mock_client

@pytest.fixture
def bloom_filter(mock_redis):
    """Create a BloomFilter instance with mocked Redis"""
    return BloomFilter(
        redis_client=mock_redis,
        expected_items=1000,
        fp_rate=0.01
    )

@pytest.fixture
def client(mock_settings):
    """FastAPI test client with mocked settings"""
    # Import here to ensure settings are mocked
    from app.main import app
    return TestClient(app)
