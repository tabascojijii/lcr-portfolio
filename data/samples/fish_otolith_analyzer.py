import cv2  # library.jsonにあるはず (opencv-python)
import numpy as np # library.jsonにあるはず
import pandas as pd # library.jsonにない場合、PyPI検索が走る
import matplotlib.pyplot as plt # PyPI検索対象
from skimage import filters # ちょっと珍しいライブラリとして

def analyze_otolith(image_path):
    # 画像読み込み
    img = cv2.imread(image_path, 0)
    # フィルタリング
    edges = filters.sobel(img)
    # 結果の集計（pandasを使用）
    df = pd.DataFrame(edges)
    print("Analysis complete. Data shape:", df.shape)
    
    plt.imshow(edges, cmap='gray')
    plt.show()

if __name__ == "__main__":
    print("Fish Otolith Analysis Tool v1.0")
    # analyze_otolith("test_image.jpg") # テスト実行用