from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
import os

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

def list_albums(creds):
    print("Fetching albums...")
    headers = {'Authorization': f'Bearer {creds.token}'}
    response = requests.get('https://photoslibrary.googleapis.com/v1/albums', headers=headers)
    albums = response.json().get('albums', [])
    for album in albums:
        print(f"Album: {album['title']} → ID: {album['id']}")

def list_photos_in_album(creds, album_id):
    print("Fetching photos in album...")
    headers = {'Authorization': f'Bearer {creds.token}'}
    body = {'albumId': album_id, 'pageSize': 10}
    response = requests.post('https://photoslibrary.googleapis.com/v1/mediaItems:search', headers=headers, json=body)
    media_items = response.json().get('mediaItems', [])
    for item in media_items:
        print(f"Photo: {item['filename']} → {item['baseUrl']}")

def main():
    creds = authenticate()
    list_albums(creds)

    album_id = input("\nPaste the album ID you want to fetch photos from: ")
    list_photos_in_album(creds, album_id)

if __name__ == '__main__':
    main()
