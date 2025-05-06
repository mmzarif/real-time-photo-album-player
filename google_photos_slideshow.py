from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
import os
import time
from io import BytesIO
from PIL import Image

SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

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
    body = {'albumId': album_id, 'pageSize': 20}
    response = requests.post('https://photoslibrary.googleapis.com/v1/mediaItems:search', headers=headers, json=body)
    media_items = response.json().get('mediaItems', [])
    photo_urls = [item['baseUrl'] + '=w800-h600' for item in media_items]
    return photo_urls

def display_slideshow(photo_urls, delay=5):
    for url in photo_urls:
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img.show()
            print(f"Showing photo: {url}")
            time.sleep(delay)
            img.close()
        except Exception as e:
            print(f"Error showing photo: {e}")

def main():
    creds = authenticate()
    album_id = input("Paste the album ID you want to show: ")
    photo_urls = get_photos_in_album(creds, album_id)

    if not photo_urls:
        print("No photos found in album!")
        return

    while True:
        display_slideshow(photo_urls)

if __name__ == '__main__':
    main()
