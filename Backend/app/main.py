from fastapi import FastAPI

app = FastAPI(
    title = "AI SQL Assistant API",
    version="1.0.0",
)

@app.get("/")
async def root():
    return {"message": "Welcome to the AI SQL Assistant API!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "The API is running smoothly."
        }