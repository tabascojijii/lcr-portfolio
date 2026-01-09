# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import csv

def main():
    print("--- Artifact Generation Test Starting ---")

    # 1. パスの設定（新しいマウント構造に対応）
    # LCR が /app/input と /app/output を用意している想定
    input_path = "/app/input/sample.jpg" # 既存の画像
    output_dir = "/app/output"
    
    # 入力画像がない場合のフォールバック（デバッグ用）
    if not os.path.exists(input_path):
        print("Input not found, creating a dummy image...")
        img = np.zeros((200, 200, 3), np.uint8)
        cv2.putText(img, "LCR TEST", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    else:
        print("Loading input image: " + input_path)
        img = cv2.imread(input_path)

    # 2. 画像処理（エッジ検出：OpenCV 2.4 でも確実に動く処理）
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    # 3. 成果物の保存
    img_output = os.path.join(output_dir, "processed_edge.png")
    cv2.imwrite(img_output, edges)
    print("Saved image to: " + img_output)

    # 4. 数値データの抽出とCSV保存
    stats = {
        "mean_brightness": np.mean(gray),
        "edge_pixel_count": np.sum(edges > 0),
        "status": "SUCCESS"
    }

    csv_output = os.path.join(output_dir, "analysis_results.csv")
    with open(csv_output, 'wb') as f: # Python 2.7 は 'wb'
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        for key, value in stats.items():
            writer.writerow([key, value])
    
    print("Saved CSV to: " + csv_output)
    print("--- Artifact Generation Test Completed ---")

if __name__ == "__main__":
    main()