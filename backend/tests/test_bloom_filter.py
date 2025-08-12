import pytest
import math
from unittest.mock import Mock
from app.BloomFilter import BloomFilter

class TestBloomFilter:
    """Unit tests for BloomFilter class"""
    
    def test_bloom_filter_initialization(self, mock_redis):
        """Test BloomFilter initialization with correct parameters"""
        bf = BloomFilter(
            redis_client=mock_redis,
            expected_items=1000,
            fp_rate=0.01
        )
        
        assert bf.expected_items == 1000
        assert bf.fp_rate == 0.01
        assert bf.redis_key == "bloom:passwords"
        assert bf.redis_client == mock_redis
        assert bf.bit_size > 0
        assert bf.num_hashes > 0
    
    def test_calculate_bit_size(self, mock_redis):
        """Test bit size calculation formula"""
        bf = BloomFilter(
            redis_client=mock_redis,
            expected_items=1000,
            fp_rate=0.01
        )
        
        # Expected formula: m = -n * ln(p) / (ln(2)^2)
        expected_size = int(-1000 * math.log(0.01) / (math.log(2)**2))
        assert bf.bit_size == expected_size
    
    def test_calculate_hash_count(self, mock_redis):
        """Test hash function count calculation"""
        bf = BloomFilter(
            redis_client=mock_redis,
            expected_items=1000,
            fp_rate=0.01
        )
        
        # Expected formula: k = (m/n) * ln(2)
        expected_hashes = int((bf.bit_size / 1000) * math.log(2))
        assert bf.num_hashes == expected_hashes
    
    def test_get_bit_positions(self, bloom_filter):
        """Test bit position generation"""
        positions = bloom_filter._get_bit_positions("test_password")
        
        assert len(positions) == bloom_filter.num_hashes
        assert all(0 <= pos < bloom_filter.bit_size for pos in positions)
        assert all(isinstance(pos, int) for pos in positions)
    
    def test_add_password(self, bloom_filter, mock_redis):
        """Test adding a password to the bloom filter"""
        test_password = "test_password_123"
        
        bloom_filter.add(test_password)
        
        # Verify Redis pipeline was called
        mock_redis.pipeline.assert_called()
        # Verify pipeline setbit was called (pipeline is the mock that gets returned)
        pipeline_mock = mock_redis.pipeline.return_value
        pipeline_mock.setbit.assert_called()
        pipeline_mock.execute.assert_called()
    
    def test_check_password_exists(self, bloom_filter, mock_redis):
        """Test checking a password that exists"""
        # Mock pipeline to return 1 for all getbit calls (password exists)
        pipeline_mock = mock_redis.pipeline.return_value
        pipeline_mock.execute.return_value = [1, 1, 1, 1, 1]
        
        result = bloom_filter.check("existing_password")
        
        assert result is True
        mock_redis.pipeline.assert_called()
        pipeline_mock.getbit.assert_called()
        pipeline_mock.execute.assert_called()
    
    def test_check_password_not_exists(self, bloom_filter, mock_redis):
        """Test checking a password that doesn't exist"""
        # Mock pipeline to return 0 for one getbit call (password doesn't exist)
        pipeline_mock = mock_redis.pipeline.return_value
        pipeline_mock.execute.return_value = [1, 0, 1, 1, 1]
        
        result = bloom_filter.check("non_existing_password")
        
        assert result is False
    
    def test_consistent_hashing(self, bloom_filter):
        """Test that the same input produces the same bit positions"""
        password = "consistent_test"
        
        positions1 = bloom_filter._get_bit_positions(password)
        positions2 = bloom_filter._get_bit_positions(password)
        
        assert positions1 == positions2
