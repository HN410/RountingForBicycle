import json 
import numpy as np 
import pandas as pd 
import os
import glob
import pathlib
import xml.etree.ElementTree as ET 

OUT_OF_RANGE_ERROR = "範囲外です．"
ALREADY_RENAMED = "すでにリネームされています"

SETTINGS_FILE = "settings.json"
GSI_DATA_FOLDER = "gsi_data_folder" # 国土地理院からダウンロードしたデータを入れたフォルダ
CENTER_AREA_FOLDER = "5339" # 今回使うエリアのフォルダ 使える地域を広げたいときはこれを選べるように
MAP_RANGE = [[35.333333333, 36.0], [139.0,140.0]] # 扱える範囲
SPLIT_N_UNITS = [8, 10] 
SPLIT_N = [SPLIT_N_UNITS[0], SPLIT_N_UNITS[0] * SPLIT_N_UNITS[1]] # フォルダの階層ごとのマップの分割数
TARGET_FOLDER_SUFFIX = "DEM5A"
DIVIDERS = [[ (ran[1] - ran[0]) / split_n for ran in MAP_RANGE] for split_n in SPLIT_N]
FILE_SUFFIX = ".xml"
FOLDER_PREFIX = "_"
MATRIX_SIZE = [150, 225] #ほとんどのファイルでこれは固定
MINI_DIVIDER = [ (ran[1] - ran[0]) / (divider * SPLIT_N[1]) for ran, divider in zip(MAP_RANGE, MATRIX_SIZE)] # 1ファイル内でどこかを割り出すときに使う
INVALID_VALUE = -1
INVALID_TAG = "データなし"

class ElevationGetter():
    # 緯度経度両方を格納するデータは緯度を先に格納する

    def __init__(self, settings_file = SETTINGS_FILE):
        with open(settings_file) as f:
            self.settings = json.load(f)
        # 標高データが読み込まれる空リストを作っておく
        self.data_list = self.nestingNoneList([SPLIT_N_UNITS[0], SPLIT_N_UNITS[0], 
                                                SPLIT_N_UNITS[1], SPLIT_N_UNITS[1]])
        
    
    # sizeのサイズの空リストを作る
    @classmethod
    def nestingNoneList(cls, size):
        if(size):
            return [cls.nestingNoneList(size[1:]) for i in range(size[0])]
        else:
            return None
    
    
    # その座標のデータがどのファイルに属するか調べる
    # 返されるのはインデックスのみ
    @staticmethod
    def searchFileIndices(coordinates):
        dividents = [co - ran[0] for co, ran in zip(coordinates, MAP_RANGE)]
        if(dividents[0] < 0 or dividents[1] < 0):
            raise ValueError(OUT_OF_RANGE_ERROR)
        res = [[int(divident // divider) for divident, divider in zip(dividents, divider_list)] for divider_list in DIVIDERS]
        res = res[0] + [divident % (SPLIT_N_UNITS[1]) for divident in res[1]]
        return res

        # resはファイルの番号を示すリストになる
        # 以下のようにパスを接合すれば求めたファイルが見つかる

    # searchFileIndicesで得たインデックスを入力して，目的のファイルのパスを得る
    def getFilePathFromIndices(self, indices):
        data_folder = os.path.join(self.settings[GSI_DATA_FOLDER], CENTER_AREA_FOLDER)
        file_name = os.path.join(data_folder, FOLDER_PREFIX + str(indices[0]) + str(indices[1]))
        file_name = os.path.join(file_name, "" + str(indices[2]) + str(indices[3]) + FILE_SUFFIX)
        return file_name


    # 使いやすいようにデータをリネームする
    # 一度実行すればもう実行しなくてよい
    def renameData(self):
        data_folder = os.path.join(self.settings[GSI_DATA_FOLDER], CENTER_AREA_FOLDER)
        # 検索しやすいようにリネーム
        # フォルダを”_番号”の形式に統一
        rename_list = glob.glob(os.path.join(data_folder,"*" + TARGET_FOLDER_SUFFIX))
        if(len(rename_list) == 0):
            print(ALREADY_RENAMED)
            return 
        for path in rename_list:
            os.rename(path, os.path.join(data_folder,FOLDER_PREFIX + path[-8:-6]))

        # ファイル名を"番号.xml"の形式に統一
        rename_list = glob.glob(os.path.join(
                os.path.join(data_folder, FOLDER_PREFIX + "*"), "*" + FILE_SUFFIX)) 
        for path in rename_list:
            parent_path = pathlib.Path(path).parent
            os.rename(path, os.path.join(parent_path, path[-21:-19] + FILE_SUFFIX))

    # xmlファイルの標高データのパース時に使用
    @staticmethod
    def elevationElementsParser(element):
        element_list = element.split(",")
        if(element_list[0] == INVALID_TAG):
            return INVALID_VALUE
        return float(element_list[1])


    # xmlファイルパスを入力し，numpy arrayで標高の行列を返す
    # MATRIX_SIZEからもわかるように，[経度方向, 緯度方向]の行列
    # 経度方向は北から南，緯度方向は西から東 (xmlファイルの順番と変わってない)
    @classmethod
    def getElevationMatrixFromFile(cls, file_name):
        tree = ET.parse(file_name)
        root = tree.getroot()
        # 開始地点
        start_point = root[2][7][3][0][1].text
        start_point = [int(point) for point in start_point.split(" ")]
        start_point.reverse()

        # 標高データを得る
        elevation = root[2][7][2][0][1].text.strip()
        elevation = elevation.split("\n", )
        elevation = [ cls.elevationElementsParser(element) for element in  elevation ]
        # start_pointに基づき，データを埋めていく
        data = None

        # 末尾のデータなしを埋める
        data_len = (MATRIX_SIZE[0]  - start_point[0])* MATRIX_SIZE[1] - start_point[1]
        if(len(elevation) != data_len):
            # 末尾のデータなしが省略されている
            elevation = elevation + [INVALID_VALUE] * (data_len - len(elevation))

        if(start_point[0] == 0 and start_point[1] == 0):
            # 全域にデータあり
            data = np.array(elevation).reshape(MATRIX_SIZE)
        else:
            # 途中からデータが始まる
            data = INVALID_VALUE * np.ones(MATRIX_SIZE, dtype = np.float64)
            if(start_point[1] != 0):
                # 横方向で途中からデータがあるとき
                # 半端な一行と残りの行で別々に
                strip = np.array(elevation[:MATRIX_SIZE[1] - start_point[1]])
                data[start_point[0], start_point[1]:] = strip
                if(start_point[0] != MATRIX_SIZE[0] - 1):
                    # 最後の行にしかデータがないとき以外
                    elevation = np.array(elevation[MATRIX_SIZE[1] - start_point[1]:])
                    elevation = elevation.reshape((-1, MATRIX_SIZE[1]))
                    data[start_point[0] + 1: ] = elevation
            else:
                # データの始まりと行の始まりが一致
                elevation = np.array(elevation)
                elevation = elevation.reshape((-1, MATRIX_SIZE[1]))
                data[start_point[0]:] = elevation
        return data

    # 入力された緯度，経度の標高を返す
    def getElevation(self, coordinates: list):
        indices = self.searchFileIndices(coordinates)
        data = self.data_list[indices[0]][indices[1]][indices[2]][indices[3]]
        if(data is None):
            # まだ読み込んでいない
            file_path = self.getFilePathFromIndices(indices)
            data = self.getElevationMatrixFromFile(file_path)
            self.data_list[indices[0]][indices[1]][indices[2]][indices[3]] = data
        
        # 余り
        residences = [ coord % divider for coord, divider in zip(coordinates, DIVIDERS[1])]
        residences[0] = DIVIDERS[1][0] - residences[0]
        ans_indices = [ int(res // divider) for res, divider in zip(residences, MINI_DIVIDER)]

        return data[ans_indices[0], ans_indices[1]]


        



