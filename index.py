import pytesseract as tess
from PIL import Image, ImageEnhance

tess.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.open('321321321.jpg')

# Preprocessing to improve OCR accuracy
img = img.convert('L') # Grayscale
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(2.0) # Increase contrast

custom_config = r'-l khm+eng --oem 3 --psm 6'

text = tess.image_to_string(img, config=custom_config)

with open('mytext5.txt', 'w', encoding='utf-8') as file:
    file.write(text)