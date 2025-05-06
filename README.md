Copy .env.example to .env and fill in your album ID:
cp .env.example .env

#To run server:
uvicorn photo_frame_api:app --host 0.0.0.0 --port 8000
