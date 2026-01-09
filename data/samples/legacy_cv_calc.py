# -*- coding: utf-8 -*-
# 研究現場で使われていた画像処理プロトタイプ

import cv2
import numpy as np

def process_image():
    print "Loading image..."
    # シグネチャ: OpenCV 2.x 系の定数 (CV_ で始まるもの)
    # これらは OpenCV 3 以降では cv2.COLOR_BGR2GRAY などに変更されている
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 判定エンジンに cv2 を検出させるためのダミー処理
    print "Image shape:", img.shape

if __name__ == "__main__":
    process_image()