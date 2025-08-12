import redis
import mmh3
import math
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import hashlib

# Connect to Redis
# redis_client = redis.Redis(
#     host='localhost',  
#     port=6379,
#     decode_responses=False
# )


class BloomFilter:

  def __init__(self, redis_client, expected_items=1_000_000, fp_rate =0.001, ):
    """
    Calcaulte the optimal size & number of hash functions
    """
    self.expected_items = expected_items
    self.fp_rate = fp_rate

    self.bit_size = self._calculate_bit_size()
    self.num_hashes = self._calculate_hash_count()
    self.redis_key = "bloom:passwords"
    self.redis_client = redis_client
  
  def _calculate_bit_size(self):
    """
    if n = expected items and p = false positive rate, we will need m bits
    m = -n * ln(p)  / (ln(2)^2)
    """
    return -self.expected_items * math.log(self.fp_rate) / (math.log(2)**2)
  

  def _calculate_hash_count(self):
    """
    if m = bit size, and n = expected items, we will need k hash functions (but we'll actually do something tricky because k hash functions is expensive)
    k = (m/n) * ln(2)
    
    source: https://en.wikipedia.org/wiki/Bloom_filter#Optimal_number_of_hash_functions
    """
    return (self.bit_size / math.log(2))
  


  def _get_bit_positions(self, item:str):
    """
    so instead of k hash functions, we'll use 2 base hashes to generate k positions

    following paper describes using 2 hash functions to simulate additional hash functions g(x) = h1(x) + i*h2(x)
    https://www.eecs.harvard.edu/~michaelm/postscripts/rsa2008.pdf
    """
    # two independent hash vals

    hash1 = mmh3.hash(item, seed=0)
    hash2 = mmh3.hash(item, seed=hash1) # seed preventing correlation

    positions = []
    for i in range(self.num_hashes):
      position = (hash1 + i * hash2) % self.bit_size
      positions.append(position)
    return positions

  def add(self, password_hash):
    """
    calculating and adding bits to Redis to persist

    SETBIT key offset value

    https://redis.io/docs/latest/commands/setbit/
    """
    positions = self._get_bit_positions(password_hash)

    #set bits in redis using Redis pipeline
    pipe = self.redis_client.pipeline()
    for pos in positions:
      pipe.setbit(self.redis_key, pos, 1)
    pipe.execute()
  

  def check(self, password_hash):
    """
    check if all k bits are set to 1
    """

    positions = self._get_bit_positions(password_hash)

    pipe = self.redis_client.pipeline()
    for pos in positions:
      pipe.getbit(self.redis_key, pos)
      
    redis_bits = pipe.execute()
    for bit in redis_bits:
      if bit == 0:
        return False
    return True