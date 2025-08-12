from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import redis
from app.BloomFilter import BloomFilter

redis_client = None
bloom_filter = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, bloom_filter
    
    print("Connecting to Redis")
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=False
    )
    
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

@app.post("/check")
async def check_password(password):
    if not bloom_filter:
        raise HTTPException(status_code=503)
    
    #we are hashing here because we dont want to actually store real passwords
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    is_compromised = bloom_filter.check(password_hash)
    return {
        "compromised": is_compromised
    }

@app.post("/add")
async def add_password(password):
    if not bloom_filter:
        raise HTTPException(status_code=503)

    #we are hashing here because we dont want to actually store real passwords
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    bloom_filter.add(password_hash)
    return {"added": True}

@app.get("/")
async def root():
  return {"status":"alive", "message": "API is running"}