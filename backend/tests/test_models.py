import pytest
from pydantic import ValidationError
from app.models import (
    PasswordRequest,
    CheckResponse,
    AddResponse,
    StatsResponse,
    StatusResponse
)

class TestModels:
    """Tests for Pydantic models"""
    
    def test_password_request_valid(self):
        """Test valid PasswordRequest"""
        request = PasswordRequest(password="test_password_123")
        assert request.password == "test_password_123"
    
    def test_password_request_empty_password(self):
        """Test PasswordRequest with empty password - should raise validation error"""
        with pytest.raises(ValidationError):
            PasswordRequest(password="")
    
    def test_password_request_missing_password(self):
        """Test PasswordRequest with missing password field"""
        with pytest.raises(ValidationError):
            PasswordRequest()
    
    def test_check_response_valid(self):
        """Test valid CheckResponse"""
        response = CheckResponse(
            compromised=True,
            message="Password found in database"
        )
        assert response.compromised is True
        assert response.message == "Password found in database"
    
    def test_check_response_default_message(self):
        """Test CheckResponse with default message"""
        response = CheckResponse(compromised=False)
        assert response.compromised is False
        assert response.message == ""
    
    def test_add_response_valid(self):
        """Test valid AddResponse"""
        response = AddResponse(added=True)
        assert response.added is True
        assert response.message == "Password hash added to bloom filter"
    
    def test_add_response_custom_message(self):
        """Test AddResponse with custom message"""
        response = AddResponse(
            added=True,
            message="Custom success message"
        )
        assert response.added is True
        assert response.message == "Custom success message"
    
    def test_stats_response_valid(self):
        """Test valid StatsResponse"""
        response = StatsResponse(
            bit_size=10000,
            bits_set=500,
            num_hashes=7,
            expected_items=1000,
            false_positive_rate=0.01,
            memory_usage_mb=1.25
        )
        
        assert response.bit_size == 10000
        assert response.bits_set == 500
        assert response.num_hashes == 7
        assert response.expected_items == 1000
        assert response.false_positive_rate == 0.01
        assert response.memory_usage_mb == 1.25
    
    def test_stats_response_invalid_types(self):
        """Test StatsResponse with invalid data types"""
        with pytest.raises(ValidationError):
            StatsResponse(
                bit_size="invalid",  # Should be int
                bits_set=500,
                num_hashes=7,
                expected_items=1000,
                false_positive_rate=0.01,
                memory_usage_mb=1.25
            )
    
    def test_status_response_valid(self):
        """Test valid StatusResponse"""
        response = StatusResponse(
            status="alive",
            message="API is running"
        )
        
        assert response.status == "alive"
        assert response.message == "API is running"
    
    def test_status_response_missing_fields(self):
        """Test StatusResponse with missing required fields"""
        with pytest.raises(ValidationError):
            StatusResponse(status="alive")  # Missing message
        
        with pytest.raises(ValidationError):
            StatusResponse(message="test")  # Missing status
