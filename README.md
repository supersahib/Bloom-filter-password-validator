# Password Bloom Filter API

High-performance API for checking if passwords have been compromised in data breaches, using Redis-backed Bloom filters.

## Features

- **Space Efficient**: ~1.7MB for 1M passwords (scales to ~1GB for 600M passwords)
- **Fast Lookups**: O(k) time complexity for lookups where k is the number of hash functions
- **Low False Positive Rate**: Configurable accuracy (default 0.1% false positive rate)
- **Privacy Focused**: Never stores actual passwords, only cryptographic hashes

## How It Works

1. **Optimal Size Calculation**: Uses mathematical formulas to determine the ideal bit array size and number of hash functions based on expected items and desired false positive rate.

2. **Double Hashing**: Instead of k independent hash functions, uses 2 base hashes to generate k positions:
   - Hash count formula: `k = (m/n) * ln(2)`
   - Reference: [Wikipedia - Bloom Filter](https://en.wikipedia.org/wiki/Bloom_filter#Optimal_number_of_hash_functions)
   - Position generation: `g(x) = h1(x) + i * h2(x)`
   - Reference: [Less Hashing, Same Performance](https://www.eecs.harvard.edu/~michaelm/postscripts/rsa2008.pdf)

3. **Redis Persistence**: Stores bit array in Redis using SETBIT and GETBIT operations for fast and persistent access.

## Bloom Filter Properties

A Bloom filter is a probabilistic data structure that provides two possible outcomes:

1. **Definitely not in set**: If any bit is 0, the item was never added
2. **Possibly in set**: If all bits are 1, the item might have been added

For password checking, this behavior is acceptable because:
- False positives are tolerable (better safe than sorry)
- False negatives never occur (will never miss a breached password)

## Architecture

![Current Architecture](./currentDiagram.png)

## Features

- Core Bloom filter implementation with optimal parameters
- FastAPI endpoints with JSON request/response models
- Docker containerization (Redis + API)
- Statistics endpoint for monitoring
- Automatic connection retry logic
- Environment-based configuration (development/production)
- Comprehensive test suite
- Production deployment configurations

## API Endpoints

### Check Password

```http
POST /check
Content-Type: application/json

{
  "password": "string"
}
```

**Response:**
```json
{
  "compromised": boolean,
  "message": "string"
}
```

### Add Password

```http
POST /add
Content-Type: application/json

{
  "password": "string"
}
```

**Response:**
```json
{
  "added": boolean,
  "message": "string"
}
```

### Get Statistics

```http
GET /stats
```

**Response:**
```json
{
  "bit_size": 14377588,
  "bits_set": 40,
  "num_hashes": 7,
  "expected_items": 1000000,
  "false_positive_rate": 0.001,
  "memory_usage_mb": 1.72
}
```

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "string"
}
```

## Installation and Usage

### Prerequisites

- Python 3.8+
- Redis server
- Docker (optional)

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
4. Start Redis server
5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Development

```bash
docker-compose up --build
```

### Production Deployment

```bash
docker-compose -f deployment/docker-compose.prod.yml up -d
```

## Configuration

The application uses environment variables for configuration:

- `ENVIRONMENT`: Set to "production" for production deployment
- `REDIS_HOST`: Redis server hostname
- `REDIS_PORT`: Redis server port
- `REDIS_PASSWORD`: Redis authentication password
- `BLOOM_EXPECTED_ITEMS`: Expected number of items in the filter
- `BLOOM_FALSE_POSITIVE_RATE`: Desired false positive rate

See `backend/env.example` for a complete list of configuration options.

## Testing

Run the test suite:

```bash
cd backend
pytest tests/ -v
```
