import pytest
import os
from unittest.mock import patch
from app.config import Settings

class TestSettings:
    """Tests for configuration settings"""
    
    def test_default_settings(self):
        """Test default settings values (ignoring test environment)"""
        # Clear test environment variables temporarily
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.redis_host == "localhost"
            assert settings.redis_port == 6379
            assert settings.redis_password is None
            assert settings.redis_ssl is False
            assert settings.bloom_expected_items == 1_000_000
            assert settings.bloom_false_positive_rate == 0.001
    
    def test_environment_detection_development(self):
        """Test development environment detection"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = Settings()
            
            assert settings.is_development is True
            assert settings.is_production is False
    
    def test_environment_detection_production(self):
        """Test production environment detection"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = Settings()
            
            assert settings.is_production is True
            assert settings.is_development is False
    
    def test_environment_detection_prod(self):
        """Test 'prod' environment detection"""
        with patch.dict(os.environ, {"ENVIRONMENT": "prod"}):
            settings = Settings()
            
            assert settings.is_production is True
            assert settings.is_development is False
    
    def test_redis_url_without_password(self):
        """Test Redis URL generation without password"""
        with patch.dict(os.environ, {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "",
            "REDIS_SSL": "false",
            "REDIS_DB": "0"
        }):
            settings = Settings()
            expected_url = "redis://localhost:6379/0"
            assert settings.redis_url == expected_url
    
    def test_redis_url_with_password(self):
        """Test Redis URL generation with password"""
        with patch.dict(os.environ, {
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "secret123",
            "REDIS_SSL": "false",
            "REDIS_DB": "1"
        }):
            settings = Settings()
            expected_url = "redis://:secret123@redis.example.com:6379/1"
            assert settings.redis_url == expected_url
    
    def test_redis_url_with_ssl(self):
        """Test Redis URL generation with SSL"""
        with patch.dict(os.environ, {
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "REDIS_PASSWORD": "secret123",
            "REDIS_SSL": "true",
            "REDIS_DB": "0"
        }):
            settings = Settings()
            expected_url = "rediss://:secret123@redis.example.com:6380/0"
            assert settings.redis_url == expected_url
    
    def test_environment_variables_override(self):
        """Test that environment variables override defaults"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'REDIS_HOST': 'prod-redis.com',
            'REDIS_PORT': '6380',
            'REDIS_PASSWORD': 'prod-password',
            'REDIS_SSL': 'true',
            'BLOOM_EXPECTED_ITEMS': '5000000',
            'BLOOM_FALSE_POSITIVE_RATE': '0.0001'
        }):
            settings = Settings()
            
            assert settings.environment == "production"
            assert settings.debug is False
            assert settings.redis_host == "prod-redis.com"
            assert settings.redis_port == 6380
            assert settings.redis_password == "prod-password"
            assert settings.redis_ssl is True
            assert settings.bloom_expected_items == 5000000
            assert settings.bloom_false_positive_rate == 0.0001
    
    def test_cors_origins_default(self):
        """Test CORS origins default value"""
        settings = Settings()
        assert settings.cors_origins == ["*"]
    
    def test_api_configuration(self):
        """Test API configuration defaults"""
        settings = Settings()
        
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_workers == 1
        assert settings.api_key is None
