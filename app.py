import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
import os
import time
import pygame
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image, ImageSequence

# Load .env
load_dotenv()
ALBUM_ID = os.getenv('ALBUM_ID')

SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
CACHE_DIR = 'cache'
REFRESH_INTERVAL = 10 * 60
SLIDE_DELAY = 5

# Control state
state = {
    "paused": False,
    "next": False,
    "refresh": False
}

# FastAPI app
app = FastAPI()

# Mount static directory (serves .html, .css, .js, etc.)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/static/control.html")

@app.post("/pause")
def pause():
    state["paused"] = True
    return {"message": "Paused"}

@app.post("/resume")
def resume():
    state["paused"] = False
    return {"message": "Resumed"}

@app.post("/next")
def next_photo():
    state["next"] = True
    return {"message": "Next photo"}

@app.post("/refresh")
def refresh_album():
    state["refresh"] = True
    return {"message": "Refreshing album"}

def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_photos_in_album(creds, album_id):
    headers = {'Authorization': f'Bearer {creds.token}'}
    body = {'albumId': album_id, 'pageSize': 50}
    response = requests.post('https://photoslibrary.googleapis.com/v1/mediaItems:search', headers=headers, json=body)
    media_items = response.json().get('mediaItems', [])
    photo_data = []
    for item in media_items:
        mime = item['mimeType']
        if mime.startswith('image/') and mime != 'image/heic':
            url = item['baseUrl'] + ('=d' if mime == 'image/gif' else '=w800-h600')
            photo_data.append({'url': url, 'mime': mime})
    return photo_data

def cache_photos(photo_data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cached = []
    for idx, item in enumerate(photo_data):
        ext = 'gif' if item['mime'] == 'image/gif' else 'jpg'
        filename = os.path.join(CACHE_DIR, f'photo_{idx}.{ext}')
        if not os.path.exists(filename):
            try:
                r = requests.get(item['url'])
                with open(filename, 'wb') as f:
                    f.write(r.content)
                print(f"Cached {filename}")
            except Exception as e:
                print(f"Failed {item['url']}: {e}")
        cached.append(filename)
    return cached

def load_cache():
    if not os.path.exists(CACHE_DIR):
        return []
    return [os.path.join(CACHE_DIR, f) for f in sorted(os.listdir(CACHE_DIR)) if f.endswith(('.jpg', '.gif'))]

def display_image(screen, file):
    img = pygame.image.load(file)
    rect = img.get_rect()
    srect = screen.get_rect()
    scale = min(srect.width / rect.width, srect.height / rect.height)
    new_size = (int(rect.width * scale), int(rect.height * scale))
    img = pygame.transform.smoothscale(img, new_size)
    rect = img.get_rect(center=srect.center)
    for alpha in range(0, 256, 10):
        img.set_alpha(alpha)
        screen.fill((0, 0, 0))
        screen.blit(img, rect)
        pygame.display.flip()
        pygame.time.Clock().tick(30)
    time.sleep(SLIDE_DELAY)

def play_gif(screen, file):
    pil_img = Image.open(file)
    frames = [pygame.image.fromstring(f.copy().convert('RGBA').tobytes(), f.size, 'RGBA')
              for f in ImageSequence.Iterator(pil_img)]
    srect = screen.get_rect()
    scaled = []
    for f in frames:
        rect = f.get_rect()
        scale = min(srect.width / rect.width, srect.height / rect.height)
        size = (int(rect.width * scale), int(rect.height * scale))
        f = pygame.transform.smoothscale(f, size)
        rect = f.get_rect(center=srect.center)
        scaled.append((f, rect))
    clock = pygame.time.Clock()
    for _ in range(2):
        for f, r in scaled:
            screen.fill((0, 0, 0))
            screen.blit(f, r)
            pygame.display.flip()
            clock.tick(15)

def slideshow():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Photo Frame')
    clock = pygame.time.Clock()
    creds = authenticate()
    try:
        photo_data = get_photos_in_album(creds, ALBUM_ID)
        files = cache_photos(photo_data)
    except:
        files = load_cache()
    idx = 0
    last_refresh = time.time()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        if state["paused"]:
            continue
        if state["refresh"] or time.time() - last_refresh > REFRESH_INTERVAL:
            creds = authenticate()
            photo_data = get_photos_in_album(creds, ALBUM_ID)
            files = cache_photos(photo_data)
            last_refresh = time.time()
            state["refresh"] = False
        if state["next"]:
            idx = (idx + 1) % len(files)
            state["next"] = False
        file = files[idx]
        if file.endswith('.gif'):
            play_gif(screen, file)
        else:
            display_image(screen, file)
        idx = (idx + 1) % len(files)

def main():
    threading.Thread(target=start_api, daemon=True).start()
    slideshow()

if __name__ == '__main__':
    main()
