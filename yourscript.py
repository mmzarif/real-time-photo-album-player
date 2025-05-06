from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
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

def list_albums(service):
    albums = service.albums().list(pageSize=10).execute()
    for album in albums.get('albums', []):
        print(f"{album['title']} ({album['id']})")

def main():
    creds = authenticate()
    service = build('photoslibrary', 'v1', credentials=creds)
    list_albums(service)

if __name__ == '__main__':
    main()
