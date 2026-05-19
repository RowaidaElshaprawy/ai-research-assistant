# ── IMPORTS ──────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException  # FastAPI is our web framework
from fastapi.middleware.cors import CORSMiddleware  # allows frontend to talk to backend
from pydantic import BaseModel              # validates request/response data shapes
import uvicorn                              # the server that runs FastAPI

# SQLAlchemy is how Python talks to databases without writing raw SQL
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from agents import research_graph           # import our compiled agent pipeline


# ── DATABASE SETUP ───────────────────────────────────────────────────────────
# SQLite is a simple file-based database — perfect for small projects
# The database will be saved as research_history.db in your backend folder
DATABASE_URL = "sqlite:///./research_history.db"

# create_engine creates the connection to the database
# check_same_thread=False is required for SQLite with FastAPI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal is a factory that creates database sessions
# Think of a session like opening and closing a connection to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all our database models inherit from
Base = declarative_base()


# ── DATABASE MODEL ───────────────────────────────────────────────────────────
# This class defines what our database table looks like
# Each attribute = one column in the table
class ResearchHistory(Base):
    __tablename__ = "history"              # the table name in the database

    id = Column(Integer, primary_key=True, index=True)  # auto-incrementing ID
    query = Column(String, index=True)     # the research topic searched
    report = Column(Text)                  # the full generated report


# This creates the table in the database if it doesn't exist yet
Base.metadata.create_all(bind=engine)


# ── FASTAPI APP ──────────────────────────────────────────────────────────────
app = FastAPI(title="AI Research Assistant API")

# CORS allows your Streamlit frontend (on port 8501) to call your
# FastAPI backend (on port 8002) — without this, the browser blocks it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in production you'd restrict this to your domain
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── DATA SHAPES ──────────────────────────────────────────────────────────────
# Pydantic models define exactly what data the API accepts and returns
# FastAPI uses these to automatically validate incoming requests

class ResearchRequest(BaseModel):
    query: str   # the request body must have a "query" field that is a string

class ResearchResponse(BaseModel):
    final_report: str   # the response will have a "final_report" string


# ── ENDPOINTS ────────────────────────────────────────────────────────────────
# An endpoint is a URL your frontend can send requests to
# @app.post means this endpoint accepts POST requests (sending data)

@app.post("/research", response_model=ResearchResponse)
async def conduct_research(request: ResearchRequest):
    # async means this function can handle multiple requests at once
    # without blocking — important for slow AI operations
    try:
        # Build the initial state — every field must be present
        # even if empty, because our TypedDict requires all keys
        initial_state = {
            "query": request.query,
            "plan": "",
            "search_queries": [],
            "raw_content": [],
            "analyzed_content": "",
            "report_draft": "",
            "final_report": ""
        }

        # Run the full agent pipeline — this is where the magic happens
        # invoke() runs all 5 agents in sequence and returns the final state
        final_state = research_graph.invoke(initial_state)
        report = final_state.get("final_report", "No report generated.")

        # Save the query and report to the database for history
        db = SessionLocal()              # open a database session
        new_entry = ResearchHistory(query=request.query, report=report)
        db.add(new_entry)               # stage the new record
        db.commit()                     # save it permanently
        db.close()                      # always close the session!

        return ResearchResponse(final_report=report)

    except Exception as e:
        # If anything goes wrong, return a proper HTTP error
        # status_code=500 means "internal server error"
        raise HTTPException(status_code=500, detail=str(e))


# ── HISTORY ENDPOINT ─────────────────────────────────────────────────────────
# @app.get means this accepts GET requests (just fetching data, no body)
@app.get("/history")
def get_history():
    db = SessionLocal()
    # Query all records from the history table
    records = db.query(ResearchHistory).all()
    db.close()
    # Return a list of dicts — FastAPI automatically converts this to JSON
    return [{"id": r.id, "query": r.query} for r in records]


# ── RUN THE SERVER ───────────────────────────────────────────────────────────
# This only runs when you execute "python main.py" directly
# host="0.0.0.0" means accept connections from any IP (not just localhost)
# port=8002 is the port number your frontend will call
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)