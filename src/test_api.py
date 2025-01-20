import uvicorn
from fastapi import FastAPI
from src.routes.main_router import router as main_router
from src.setup import load_embedding_function, load_vectorstore
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize app
app = FastAPI()

# Store resources in app's state so they can be accessed in views
app.state.EMBEDDINGFUNCTION = load_embedding_function()

def update_vectorstore():
    app.state.VECTORSTORE = load_vectorstore(app.state.EMBEDDINGFUNCTION)

update_vectorstore()
scheduler = BackgroundScheduler()
scheduler.add_job(update_vectorstore, 'interval', days=1)

# Add a test route for debugging purposes
@app.get("/")
async def root():
    return {"message": "API is working!"}

# Register routes from main_router
app.include_router(main_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    scheduler.start()
