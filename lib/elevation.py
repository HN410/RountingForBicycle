import json 
import numpy as np 
import pandas as pd 
import os
import glob
import pathlib

class ElevationGetter():
    # 緯度経度両方を格納するデータは緯度を先に格納すること
    OUT_OF_RANGE_ERROR = "範囲外です．"
    ALREADY_RENAMED = "すでにリネームされています"

    SETTINGS_FILE = "settings.json"
    GSI_DATA_FOLDER = "gsi_data_folder" # 国土地理院からダウンロードしたデータを入れたフォルダ
    CENTER_AREA_FOLDER = "5339" # 今回使うエリアのフォルダ 使える地域を広げたいときはこれを選べるように
    MAP_RANGE = [[35.333333333, 36.0], [139.0,140.0]] # 扱える範囲
    SPLIT_N_UNITS = [8, 10] 
    SPLIT_N = [SPLIT_N_UNITS[0], SPLIT_N_UNITS[0] * SPLIT_N_UNITS[1]] # フォルダの階層ごとのマップの分割数
    DIVIDERS = [[ (ran[1] - ran[0]) / split_n for ran in MAP_RANGE ] for split_n in SPLIT_N]
    TARGET_FOLDER_SUFFIX = "DEM5A"
    FILE_SUFFIX = ".xml"
    FOLDER_PREFIX = "_"

    def __init__(self, settings_file = SETTINGS_FILE):
        with open(settings_file) as f:
            self.settings = json.load(f)
    

    # その座標のデータがどのファイルに属するか調べる
    # 返されるのはインデックスのみ
    def searchFileIndices(self, coordinates):
        coordinate = [35.702, 139.28]
        dividents = [co - ran[0] for co, ran in zip(coordinate, self.MAP_RANGE)]
        if(dividents[0] < 0 or dividents[1] < 0):
            raise ValueError(self.OUT_OF_RANGE_ERROR)
        res = [[int(divident // divider) for divident, divider in zip(dividents, divider_list)] for divider_list in DIVIDERS]
        res = res[0] + [divident % (self.SPLIT_N_UNITS[1]) for divident in res[1]]
        return res

        # resはファイルの番号を示すリストになる
        # 以下のようにパスを接合すれば求めたファイルが見つかる

    # searchFileIndicesで得たインデックスを入力して，目的のファイルのパスを得る
    def getFilePathFromIndices(self, indices):
        data_folder = os.path.join(self.settings[self.GSI_DATA_FOLDER], self.CENTER_AREA_FOLDER)
        file_name = os.path.join(data_folder, self.FOLDER_PREFIX + str(indices[0]) + str(indices[1]))
        file_name = os.path.join(file_name, "" + str(indices[2]) + str(indices[3]) + self.FILE_SUFFIX)
        return file_name


    # 使いやすいようにデータをリネームする
    # 一度実行すればもう実行しなくてよい
    def renameData(self):
        data_folder = os.path.join(self.settings[self.GSI_DATA_FOLDER], self.CENTER_AREA_FOLDER)
        # 検索しやすいようにリネーム
        # フォルダを”_番号”の形式に統一
        rename_list = glob.glob(os.path.join(data_folder,"*" + self.TARGET_FOLDER_SUFFIX))
        if(len(rename_list) == 0):
            print(self.ALREADY_RENAMED)
            return 
        for path in rename_list:
            os.rename(path, os.path.join(data_folder,self.FOLDER_PREFIX + path[-8:-6]))

        # ファイル名を"番号.xml"の形式に統一
        rename_list = glob.glob(os.path.join(
                os.path.join(data_folder, self.FOLDER_PREFIX + "*"), "*" + self.FILE_SUFFIX)) 
        for path in rename_list:
            parent_path = pathlib.Path(path).parent
            os.rename(path, os.path.join(parent_path, path[-21:-19] + self.FILE_SUFFIX))

