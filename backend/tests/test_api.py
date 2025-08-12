import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app

class TestAPI:
    """Integration tests for FastAPI endpoints"""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["message"] == "API is running"
    
    @patch('app.main.bloom_filter')
    @patch('app.main.redis_client')
    def test_check_password_safe(self, mock_redis, mock_bloom_filter, client):
        """Test checking a safe password"""
        # Mock bloom filter to return False (password not compromised)
        mock_bloom_filter.check.return_value = False
        
        response = client.post("/check", json={"password": "safe_password_123"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["compromised"] is False
        assert "safe" in data["message"].lower()
    
    @patch('app.main.bloom_filter')
    @patch('app.main.redis_client')
    def test_check_password_compromised(self, mock_redis, mock_bloom_filter, client):
        """Test checking a compromised password"""
        # Mock bloom filter to return True (password is compromised)
        mock_bloom_filter.check.return_value = True
        
        response = client.post("/check", json={"password": "compromised_password"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["compromised"] is True
        assert "compromised" in data["message"].lower()
    
    @patch('app.main.bloom_filter')
    @patch('app.main.redis_client')
    def test_add_password(self, mock_redis, mock_bloom_filter, client):
        """Test adding a password to the bloom filter"""
        mock_bloom_filter.add.return_value = None
        
        response = client.post("/add", json={"password": "new_compromised_password"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["added"] is True
        assert "added" in data["message"].lower()
        mock_bloom_filter.add.assert_called_once()
    
    @patch('app.main.bloom_filter')
    @patch('app.main.redis_client')
    def test_stats_endpoint(self, mock_redis, mock_bloom_filter, client):
        """Test the stats endpoint"""
        # Mock bloom filter properties
        mock_bloom_filter.bit_size = 10000
        mock_bloom_filter.num_hashes = 7
        mock_bloom_filter.expected_items = 1000
        mock_bloom_filter.fp_rate = 0.01
        mock_bloom_filter.redis_key = "bloom:passwords"
        
        # Mock Redis bitcount
        mock_redis.bitcount.return_value = 500
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["bit_size"] == 10000
        assert data["bits_set"] == 500
        assert data["num_hashes"] == 7
        assert data["expected_items"] == 1000
        assert data["false_positive_rate"] == 0.01
        assert "memory_usage_mb" in data
    
    def test_check_password_invalid_json(self, client):
        """Test check endpoint with invalid JSON"""
        response = client.post("/check", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_add_password_invalid_json(self, client):
        """Test add endpoint with invalid JSON"""
        response = client.post("/add", json={"wrong_field": "value"})
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.main.bloom_filter', None)
    def test_endpoints_when_bloom_filter_not_initialized(self, client):
        """Test endpoints when bloom filter is not initialized"""
        response = client.post("/check", json={"password": "test"})
        assert response.status_code == 503
        
        response = client.post("/add", json={"password": "test"})
        assert response.status_code == 503
        
        response = client.get("/stats")
        assert response.status_code == 503
