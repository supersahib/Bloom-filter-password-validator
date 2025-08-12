# Password Validator using Bloom Filter (and Redis)

Hihg performance API for checking if passwords have been compromised in data breaches, using Redis-backed Bloom filters

- **Space Efficient**: metrics to be added*
- **Fast Lookups**: metrics to be added*
- **Low False Positive Rate**: Configurable accuracy (default 0.1% FP rate)
- **REST API**: FastAPI backend with automatic documentation
- **Privacy Focused**: Never stores actual passwords, only hashes
- **Scalable**: Sharded Bloom filter design for distributed systems

### Proposed Architecture

![[Screenshot 2025-08-11 at 8.14.40 PM.png|600x600]]


### how it works

1. **Optimal size calculation** - uses math formulas to determine the ideal bit array size and # of hash functions, based on expected items and desired FP rate
2. **Double hashing** - instead of k independent hash functions, use 2 base hashes to generate k positions
3. **Redis persistence** - stores bit array in REdis using SETBIT & GETBIT operations for fast & persisten access

### What i've learned about Bloom filters
- Bloom filter is a probablistic data structure that tells you one of 2 things:
	1) data is DEFINITELY not in set --> if any bit is 0, item was never added
	2) data is POSSIBLY in set --> if all bits are 1, item might have been added

- for password checking this is okay because:
	- false positives are acceptable  (we're better safe than sorry here)
	- false negatives never occur (will never miss a breached password)
