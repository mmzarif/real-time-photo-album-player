from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Shared control state
state = {
    "paused": False,
    "next": False,
    "refresh": False
}

@app.get("/")
def root():
    return {
        "paused": state["paused"],
        "next": state["next"],
        "refresh": state["refresh"]
    }

@app.post("/pause")
def pause():
    state["paused"] = True
    return {"message": "Paused slideshow"}

@app.post("/resume")
def resume():
    state["paused"] = False
    return {"message": "Resumed slideshow"}

@app.post("/next")
def next_photo():
    state["next"] = True
    return {"message": "Skipping to next photo"}

@app.post("/refresh")
def refresh_album():
    state["refresh"] = True
    return {"message": "Album refresh requested"}
