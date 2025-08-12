from fastapi import FastAPI


app = FastAPI(title="Password Bloom Filter API")

@app.get("/")
async def root():
  return {"status":"alive", "message": "API is running"}