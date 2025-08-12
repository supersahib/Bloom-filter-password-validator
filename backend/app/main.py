from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import redis
from app.BloomFilter import BloomFilter
from app.models import PasswordRequest, CheckResponse, AddResponse, StatsResponse, StatusResponse
from app.config import settings
import hashlib
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

redis_client = None
bloom_filter = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, bloom_filter
    
    logger.info(f"Starting application in {settings.environment} mode")
    logger.info(f"Connecting to Redis at {settings.redis_host}:{settings.redis_port}")
    logger.info(f"Redis SSL: {settings.redis_ssl}")

    retry_count = 0
    
    while retry_count < settings.redis_max_retries:
        try:
            # Create Redis connection with proper configuration
            redis_kwargs = {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
                "decode_responses": False,
                "socket_connect_timeout": settings.redis_connection_timeout,
                "socket_timeout": settings.redis_connection_timeout,
            }
            
            # Add password if provided
            if settings.redis_password:
                redis_kwargs["password"] = settings.redis_password
            
            # Add SSL configuration for production
            if settings.redis_ssl:
                redis_kwargs["ssl"] = True
                redis_kwargs["ssl_cert_reqs"] = None
            
            redis_client = redis.Redis(**redis_kwargs)
            redis_client.ping()
            logger.info("Redis connection successful")
            break
        
        except redis.ConnectionError as e:
            retry_count += 1
            logger.warning(f"Redis not ready, retry {retry_count}/{settings.redis_max_retries}...")
            if retry_count == settings.redis_max_retries:
                logger.error(f"Failed to connect to Redis after {settings.redis_max_retries} attempts: {e}")
                raise Exception(f"Failed to connect to Redis: {e}")
            time.sleep(2)

    logger.info("Initializing Bloom Filter")
    bloom_filter = BloomFilter(
        redis_client=redis_client,
        expected_items=settings.bloom_expected_items,
        fp_rate=settings.bloom_false_positive_rate
    )
    # Update redis key from settings
    bloom_filter.redis_key = settings.bloom_redis_key
    
    logger.info(f"Bloom filter ready: {bloom_filter.bit_size:,} bits")
    logger.info(f"Expected items: {settings.bloom_expected_items:,}")
    logger.info(f"False positive rate: {settings.bloom_false_positive_rate}")
    
    yield
  
    if redis_client:
        logger.info("Closing Redis connection")
        redis_client.close()

app = FastAPI(
    title="Password Bloom Filter API",
    description="A secure password validation API using Bloom Filters",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        if redis_client:
            redis_client.ping()
        return StatusResponse(
            status="healthy", 
            message=f"API running in {settings.environment} mode"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    if not bloom_filter or not redis_client:
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    try:
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
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")