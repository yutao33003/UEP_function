import os
import cv2
import numpy as np
import pytesseract
from pathlib import Path
import winshell


def main():
    path = input("輸入辨識圖片路徑：")
    path = Path(path)
    with open(path, "rb") as f:
        img_path = np.frombuffer(f.read(), np.uint8)
    image = cv2.imread(img_path)
    if image is None:
        print("圖片讀取失敗，請確認路徑與檔案格式！")
        return

    # 灰階 + 二值化，提升辨識效果
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    num = int(input("1 輸出文字 2 輸出 PDF: "))
    if num == 1:
        text = pytesseract.image_to_string(thresh, lang = "chi_tra+eng")
        print("辨識結果：")
        print(text)
    else:
        data = pytesseract.image_to_pdf_or_hocr(thresh, lang = "chi_tra+eng", extension = "pdf")
        base_name = os.path.splitext(os.path.basename(path))[0]
        with open(winshell.desktop() + f"/{base_name}_OCR.pdf", "wb") as f:
            f.write(data)
    
if __name__ == "__main__":
    main()