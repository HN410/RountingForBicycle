import osmnx as ox
from lib.gradDistance import GradDistance
from lib.elevation import ElevationGetter

elevation = ElevationGetter()
elevation.renameData() # 初回のみ必要

grad_distance = GradDistance()
G = ox.graph_from_point(center_point=(35.68129279199922, 139.76679100155133), network_type="drive", dist=1000)
G = grad_distance.addGradDisToGraph(G)

# 開始地点，終着地点を設定
start_point = (35.70961506063877, 139.72698640044294)
end_point = (35.671849025355996, 139.74144749037666)

start_node = ox.get_nearest_node(G, start_point)
end_node = ox.get_nearest_node(G, end_point)
shortest_path_grad = ox.shortest_path(G, start_node, end_node, weight = "GradDist")

# 表示
ox.plot_route_folium(G, shortest_path_grad)
