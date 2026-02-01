"""
Run the FastAPI application
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # Use 127.0.0.1 for Windows compatibility
        port=8001,         # Changed port to avoid conflicts
        reload=True
    )
