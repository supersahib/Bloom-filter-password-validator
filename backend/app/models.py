from pydantic import BaseModel, Field

# Request models
class PasswordRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Password to check or add")

# Response models
class CheckResponse(BaseModel):
    compromised: bool
    message: str = ""

class AddResponse(BaseModel):
    added: bool
    message: str = "Password hash added to bloom filter"

class StatsResponse(BaseModel):
    bit_size: int
    bits_set: int
    num_hashes: int
    expected_items: int
    false_positive_rate: float
    memory_usage_mb: float

class StatusResponse(BaseModel):
    status: str
    message: str
