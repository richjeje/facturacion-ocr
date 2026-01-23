from pdf2image import convert_from_path
import cv2
import pytesseract
import numpy as np

images = convert_from_path("imagenes/PFIX.pdf")
texto = ""
for img in images:
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    texto += pytesseract.image_to_string(img_cv, lang="spa+eng") + "\n"
print(texto)
