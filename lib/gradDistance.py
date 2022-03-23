from elevation import ElevationGetter
import json 
import numpy as np 
import pandas as pd 
import os
import glob
import pathlib
import xml.etree.ElementTree as ET 
import folium
import osmnx as ox
import pandas as pd
import numpy as np 
import geopandas as gpd
from lib.elevation import ElevationGetter
import pickle

R = 6370
L_D = 2 * np.pi * R / 360 * 1000 # 1度当たりの距離(m)
L_D * 0.0002 # 20m くらい
# 2e-4度の差が大体20m，この幅に区切って傾斜を調べる
dist_threshold = 20 # 20m間隔で傾斜を調べる
grad_coef = 10000

# 道路グラフに傾斜を考慮した距離の欄を追加する
class GradDistance():
    # hate_coef ... 傾斜をどれだけ避けるか
    def __init__(self, hate_coef = 1):
        self.elevation_getter = ElevationGetter()
        self.l_d = hate_coef * grad_coef

    # 無向グラフだと仮定して，傾斜があったらすべて値を大きくする
    def calcGradDisUnit(self, x0, y0, x1, y1, dist):
        ele0 = self.elevation_getter.getElevation([y0, x0]) # 緯度が先なので注意
        ele1 = self.elevation_getter.getElevation([y1, x1])
        grad = np.abs(ele0 - ele1) / dist
        return dist * (1 + grad_coef * (grad ** 2))


    # 傾斜も考慮に入れた距離を算出
    # 引数は２地点の緯度経度
    def calcGradDistance(self, x0, y0, x1, y1):
        dist = np.sqrt((x0-x1) ** 2 + (y0 - y1) ** 2)
        dist *= self.l_d

        if(dist > dist_threshold):
            # 一定以上の長さなら，分割して高度を計算
            divider = int(dist // dist_threshold) + 1
            dist_unit = dist / divider
            x_unit, y_unit = (x1-x0)/divider , (y1 - y0) / divider
            return np.array([self.calcGradDisUnit(x0 + x_unit*i, y0 + y_unit*i, x0 + x_unit*(i+1) , y0 + y_unit * (i+1), dist_unit) for i in range(divider)]).sum()
        else:
            return self.calcGradDisUnit(x0, y0, x1, y1, dist)

    # LineString形式からその勾配を考慮した距離を導く
    def lineStringToGradDist(self, shape):
        x, y = shape.coords.xy
        n = len(x)
        return np.array([self.calcGradDistance(x[i], y[i], x[i + 1], y[i+1])  for i in range(n - 1)]).sum()

    
        
