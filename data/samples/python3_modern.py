# Python 3.x のモダンなサンプル

import os

def greet(name: str) -> None:
    # シグネチャ1: 関数としての print()
    # シグネチャ2: f-string
    print(f"Hello, {name}!")
    
    # シグネチャ3: 整数除算 (3.x では 0.5 になる)
    print(f"1 / 2 = {1 / 2}")

if __name__ == "__main__":
    greet("LCR User")