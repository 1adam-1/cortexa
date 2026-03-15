from PIL import Image
import pytesseract
import cv2

file1 = "index_02.JPG"
im1 = cv2.imread(file1)
gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)

blur = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (3,13))

dilate = cv2.dilate(thresh, kernal, iterations=1)

cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if len(cnts) == 2 else cnts[1]
cnts = sorted(cnts, key=lambda x: cv2.boundingRect(x)[0])

for c in cnts:
    x,y,w,h = cv2.boundingRect(c)
    if w >20 and h > 200:
        roi = im1[y:y+h, x:x+w]
        cv2.rectangle(im1, (x, y), (x + w, y + h), (36,255,12), 2)
        text = pytesseract.image_to_string(roi)
        text = text.split("\n")
        for t in text:
            t=t.strip()
            t=t.split(" ")[0]
            print(t)

