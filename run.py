import uvicorn

if __name__ == "__main__":
    print("Starting AI-powered Business Analytics Assistant ML Microservice...")
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
