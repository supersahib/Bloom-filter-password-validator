from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import redis
from app.BloomFilter import BloomFilter
from app.models import PasswordRequest, CheckResponse, AddResponse, StatsResponse, StatusResponse
import hashlib
import time
import os

redis_client = None
bloom_filter = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, bloom_filter
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    
    print(f"Connecting to Redis at {redis_host}:{redis_port}")

    max_retries = 5
    retry_count = 0
    
    #retry logic for container startup timing

    while retry_count < max_retries:
      try:
          redis_client = redis.Redis(
              host=redis_host,
              port=redis_port,
              decode_responses=False
          )
          redis_client.ping()
          print("Redis connection successful")
          break
      
      except redis.ConnectionError as e:
          retry_count += 1
          print(f"Redis not ready, retry {retry_count}/{max_retries}...")
          if retry_count == max_retries:
              raise Exception(f"Failed to connect to Redis: {e}")
          time.sleep(2)

    print("Initializing Bloom Filter")
    bloom_filter = BloomFilter(
        redis_client=redis_client,
        expected_items=1_000_000,
        fp_rate=0.001
    )
    print(f"Bloom filter ready: {bloom_filter.bit_size:,} bits")
    
    yield
  
    if redis_client:
        redis_client.close()

app = FastAPI(title="Password Bloom Filter API", lifespan=lifespan)

@app.post("/check", response_model=CheckResponse)
async def check_password(request: PasswordRequest):
    if not bloom_filter:
        raise HTTPException(status_code=503, detail="Bloom filter not initialized")
    
    #we are hashing here because we dont want to actually store real passwords
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    
    is_compromised = bloom_filter.check(password_hash)
    
    message = "Password found in compromised database" if is_compromised else "Password appears safe"
    
    return CheckResponse(
        compromised=is_compromised,
        message=message
    )

@app.post("/add", response_model=AddResponse)
async def add_password(request: PasswordRequest):
    if not bloom_filter:
        raise HTTPException(status_code=503, detail="Bloom filter not initialized")

    #we are hashing here because we dont want to actually store real passwords
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()

    bloom_filter.add(password_hash)
    return AddResponse(added=True)

@app.get("/", response_model=StatusResponse)
async def root():
    return StatusResponse(status="alive", message="API is running")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    if not bloom_filter or not redis_client:
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    # Get bit count from Redis
    bits_set = redis_client.bitcount(bloom_filter.redis_key)
    
    return StatsResponse(
        bit_size=bloom_filter.bit_size,
        bits_set=bits_set,
        num_hashes=bloom_filter.num_hashes,
        expected_items=bloom_filter.expected_items,
        false_positive_rate=bloom_filter.fp_rate,
        memory_usage_mb=bloom_filter.bit_size / (8 * 1024 * 1024)
    )