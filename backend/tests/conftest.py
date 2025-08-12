import pytest
import redis
from unittest.mock import Mock, MagicMock
from app.BloomFilter import BloomFilter
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.setbit.return_value = 0
    mock_client.getbit.return_value = 1
    mock_client.bitcount.return_value = 100
    
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
def client():
    """FastAPI test client"""
    return TestClient(app)
