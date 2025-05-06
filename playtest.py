from PIL import Image
import requests
from io import BytesIO

def display_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img.show()
