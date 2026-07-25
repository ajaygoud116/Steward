import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from lyzr import Studio

load_dotenv()

app = FastAPI(title="Travel Agent API")

studio = Studio(api_key=os.getenv("LYZR_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/travel/plan", response_model=ChatResponse)
def plan_trip(req: ChatRequest):
    agent = studio.create_agent(
        name="TravelManager",
        provider="gpt-4o",
        role="Travel planning assistant",
        goal="Help users plan trips",
        instructions="Extract destination, dates, and budget. Ask for missing info.",
    )
    result = agent.run(req.message, session_id=req.session_id)
    return ChatResponse(response=result.response, session_id=result.session_id)
