import json 
import numpy as np 
import pandas as pd 
import os
import glob

class ElevationGetter():
    # 緯度経度両方を格納するデータは緯度を先に格納すること
    OUT_OF_RANGE_ERROR = "範囲外です．"

    SETTINGS_FILE = "settings.json"
    GSI_DATA_FOLDER = "gsi_data_folder" # 国土地理院からダウンロードしたデータを入れたフォルダ
    CENTER_AREA_FOLDER = "5339" # 今回使うエリアのフォルダ 使える地域を広げたいときはこれを選べるように
    MAP_RANGE = [[35.333333333, 36.0], [139.0,140.0]] # 扱える範囲
    SPLIT_N = [8, 8 * 10] # フォルダの階層ごとのマップの分割数
    DIVIDERS = [[ (ran[1] - ran[0]) / split_n for ran in MAP_RANGE ] for split_n in SPLIT_N]

    def __init__(self, settings_file = SETTINGS_FILE):
        with open(settings_file) as f:
            self.settings = json.load(f)
    
    # その座標のデータがどのファイルに属するか調べる
    def searchFile(self, coordinates):
        coordinate = [35.702, 139.28]
        dividents = [co - ran[0] for co, ran in zip(coordinate, self.MAP_RANGE)]
        if(dividents[0] < 0 or dividents[1] < 0):
            raise ValueError(self.OUT_OF_RANGE_ERROR)
        res = [[int(divident // divider) for divident, divider in zip(dividents, divider_list)] for divider_list in DIVIDERS]
        res[1] = [divident % (self.SPLIT_N[1] // self.SPLIT_N[0]) for divident in res[1]]

        # resはファイルの番号を示すリストになる
        # 以下のようにパスを接合すれば求めたファイルが見つかる

