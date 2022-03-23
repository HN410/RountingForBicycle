from .elevation import ElevationGetter
import numpy as np 
import osmnx as ox
import numpy as np 
from lib.elevation import ElevationGetter

R = 6370
L_D = 2 * np.pi * R / 360 * 1000 # 1度当たりの距離(m)
L_D * 0.0002 # 20m くらい
# 2e-4度の差が大体20m，この幅に区切って傾斜を調べる
DIST_THRESHOLD = 20 # 20m間隔で傾斜を調べる
GRAD_COEF = 10000
DEFAULT_COLUMN_NAME = "GradDist"

# 道路グラフに傾斜を考慮した距離の欄を追加する
class GradDistance():
    # hate_coef ... 傾斜をどれだけ避けるか
    def __init__(self, hate_coef = 1, column_name = DEFAULT_COLUMN_NAME):
        self.elevation_getter = ElevationGetter()
        self.l_d = hate_coef * GRAD_COEF
        self.column_name = column_name

    # 無向グラフだと仮定して，傾斜があったらすべて値を大きくする
    def calcGradDisUnit(self, x0, y0, x1, y1, dist):
        if(dist == 0):
            return 0
        ele0 = self.elevation_getter.getElevation([y0, x0]) # 緯度が先なので注意
        ele1 = self.elevation_getter.getElevation([y1, x1])
        grad = np.abs(ele0 - ele1) / dist
        return dist * (1 + GRAD_COEF * (grad ** 2))


    # 傾斜も考慮に入れた距離を算出
    # 引数は２地点の緯度経度
    def calcGradDistance(self, x0, y0, x1, y1):
        dist = np.sqrt((x0-x1) ** 2 + (y0 - y1) ** 2)
        dist *= self.l_d

        if(dist > DIST_THRESHOLD):
            # 一定以上の長さなら，分割して高度を計算
            divider = int(dist // DIST_THRESHOLD) + 1
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


    # グラフにGradDisの項を追加する
    def addGradDisToGraph(self, G):
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
        geometryArray = gdf_edges["geometry"].to_numpy()
        gdf_edges[self.column_name] = [self.lineStringToGradDist(geo) for geo in geometryArray]
        graph_attrs = {'crs': 'epsg:4326', 'simplified': True}
        return ox.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs)
