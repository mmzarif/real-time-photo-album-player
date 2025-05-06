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
REFRESH_INTERVAL = 10 * 60  # seconds (10 min)
SLIDE_DELAY = 5  # seconds for static images

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
        mime_type = item['mimeType']
        if mime_type.startswith('image/') and mime_type != 'image/heic':
            if mime_type == 'image/gif':
                url = item['baseUrl'] + '=d'  # original GIF download
            else:
                url = item['baseUrl'] + '=w800-h600'
            photo_data.append({'url': url, 'mime': mime_type})
        else:
            print(f"Skipping unsupported file type: {mime_type}")
    return photo_data

def cache_photos(photo_data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cached_files = []
    for idx, item in enumerate(photo_data):
        ext = 'gif' if item['mime'] == 'image/gif' else 'jpg'
        filename = os.path.join(CACHE_DIR, f'photo_{idx}.{ext}')
        if not os.path.exists(filename):
            try:
                response = requests.get(item['url'])
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"Cached {filename}")
            except Exception as e:
                print(f"Failed to download {item['url']}: {e}")
        cached_files.append(filename)
    return cached_files

def load_local_cache():
    if not os.path.exists(CACHE_DIR):
        return []
    return [os.path.join(CACHE_DIR, f) for f in sorted(os.listdir(CACHE_DIR)) if f.endswith(('.jpg', '.gif'))]

def display_image(screen, filepath):
    img = pygame.image.load(filepath)
    img_rect = img.get_rect()
    screen_rect = screen.get_rect()
    scale_w = screen_rect.width / img_rect.width
    scale_h = screen_rect.height / img_rect.height
    scale = min(scale_w, scale_h)
    new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
    img = pygame.transform.smoothscale(img, new_size)
    img_rect = img.get_rect(center=screen_rect.center)
    for alpha in range(0, 256, 10):
        img.set_alpha(alpha)
        screen.fill((0, 0, 0))
        screen.blit(img, img_rect)
        pygame.display.flip()
        pygame.time.Clock().tick(30)
    time.sleep(SLIDE_DELAY)

def play_gif(screen, filepath):
    pil_img = Image.open(filepath)
    frames = [pygame.image.fromstring(frame.copy().convert('RGBA').tobytes(), frame.size, 'RGBA') 
              for frame in ImageSequence.Iterator(pil_img)]
    screen_rect = screen.get_rect()
    scaled_frames = []
    for frame in frames:
        frame_rect = frame.get_rect()
        scale_w = screen_rect.width / frame_rect.width
        scale_h = screen_rect.height / frame_rect.height
        scale = min(scale_w, scale_h)
        new_size = (int(frame_rect.width * scale), int(frame_rect.height * scale))
        frame = pygame.transform.smoothscale(frame, new_size)
        frame_rect = frame.get_rect(center=screen_rect.center)
        scaled_frames.append((frame, frame_rect))
    clock = pygame.time.Clock()
    for _ in range(2):  # loop GIF twice
        for frame, rect in scaled_frames:
            screen.fill((0, 0, 0))
            screen.blit(frame, rect)
            pygame.display.flip()
            clock.tick(15)  # ~15 FPS

def display_slideshow(image_files):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Photo Frame')
    clock = pygame.time.Clock()

    idx = 0
    last_refresh_time = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        file = image_files[idx]
        if file.endswith('.gif'):
            print(f"Playing GIF {file}")
            play_gif(screen, file)
        else:
            print(f"Showing image {file}")
            display_image(screen, file)

        idx = (idx + 1) % len(image_files)

        if time.time() - last_refresh_time > REFRESH_INTERVAL:
            print("Refreshing album...")
            try:
                creds = authenticate()
                photo_data = get_photos_in_album(creds, ALBUM_ID)
                image_files = cache_photos(photo_data)
                last_refresh_time = time.time()
            except Exception as e:
                print(f"Refresh failed, using local cache: {e}")
                image_files = load_local_cache()

def main():
    creds = authenticate()
    try:
        photo_data = get_photos_in_album(creds, ALBUM_ID)
        image_files = cache_photos(photo_data)
    except Exception as e:
        print(f"Failed to fetch from API, loading local cache: {e}")
        image_files = load_local_cache()

    if not image_files:
        print("No images available.")
        return

    display_slideshow(image_files)

if __name__ == '__main__':
    main()
