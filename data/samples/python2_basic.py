# -*- coding: utf-8 -*-
# Python 2.7 の典型的なサンプル

import sys

def check_version():
    # シグネチャ1: カッコなし print
    print "Checking system version..."
    
    # シグネチャ2: 整数除算 (2.7 では 0 になる)
    result = 1 / 2
    
    try:
        # シグネチャ3: 例外処理のカンマ構文
        val = 10 / 0
    except ZeroDivisionError, e:
        print "Error occurred:", e

if __name__ == "__main__":
    check_version()