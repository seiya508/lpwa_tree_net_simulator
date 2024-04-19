############################## experiment.py ##############################
# Experiment file for LPWA network simulation
# Note: This program needs "settings.py", "network_mod.py", and "network_io.py"
# @created      2024-01-06
# @developer    226E0214 Seiya Kinoshita
# @affiliation  Tanaka Lab. Kyutech
############################## ####### ##############################

from settings import *
from network_mod import *
from network_io import *
import numpy as np
import csv

# 実験試行回数
NUM_OF_TRIAL = 100
# *経路制御アルゴリズムの切り替えは
# settings.py - is_previous_routing を参照のこと

root = RootNode(0, (0, 0))   # ルートノード

nodes = [
    root,   # ルートノードを1つだけ必ず含める

    Node(1, (3, 3)),     Node(2, (4, 6)),     Node(3, (6, 2)),
    Node(4, (-3, -2)),   Node(5, (-5, -4)),   Node(6, (-2, -3)),
    Node(7, (3, 2)),     Node(8, (-3, 6)),    Node(9, (-2, 3)),
    Node(10, (0, -5)),   Node(11, (-5, 2)),   Node(12, (3, -4)),
    Node(13, (5, 4)),    Node(14, (-6, -6)),  Node(15, (4, -3)),
    Node(16, (-3, -5)),  Node(17, (-5, 5)),   Node(18, (6, -5)),
    Node(19, (-4, 0)),   Node(20, (5, 1)),    Node(21, (0, 5)),

    Node(22, (8, 10)),   Node(23, (-10, 3)),   Node(24, (9, -9)),
    Node(25, (-7, 9)),   Node(26, (-8, -6)),   Node(27, (-12, -8)),
    Node(28, (-11, -5)), Node(29, (10, -2)),   Node(30, (-3, 8)),
    Node(31, (13, 14)),  Node(32, (-11, -2)),  Node(33, (7, -9)),
    Node(34, (8, -11)),  Node(35, (-3, -13)),  Node(36, (14, 7)),
    Node(37, (15, -6)),  Node(38, (10, -11)),  Node(39, (10, 6)),

    Node(40, (13, -5)),  Node(41, (13, 10)),   Node(42, (3, 9)),
    Node(43, (-9, 6)),   Node(44, (-4, -10)),  Node(45, (12, -7)),
    Node(46, (-1, -9)),  Node(47, (6, -1)),    Node(48, (1, 7)),
    Node(49, (3, -7)),   Node(50, (-10, -10)), Node(51, (12, 0)),
    Node(52, (15, 2)),   Node(53, (-10, -13)), Node(54, (-7, 0)),
    Node(55, (-10, 9)),  Node(56, (9, 2)),     Node(57, (2, -10)),
    Node(58, (-6, 10)),  Node(59, (-14, 7)),   Node(60, (6, -14))
]

step = 0  # ステップ数
time = 0  # 経過予想時間
cnt = 0   # 通信回数

# 初期ネットワークの確認
print("Hello, network!")
fig, ax = nio.init_graph()
nio.update_graph(nodes, step, time, cnt, fig, ax, is_fixed_axis=True)
wait_command(nodes, step, time, cnt, fig, ax)

ave_depths = [] # ノード平均深さリスト
ave_rssis = []  # 経路平均RSSIリスト
times = []      # 復旧経過時間リスト
cnts = []       # 復旧通信回数リスト

# 反復試行実験
for i in range(NUM_OF_TRIAL):
    # ネットワーク構築
    step += 1
    root.build_network()
    res = 0
    while res != -1:
        step += 1
        print("\n========================= Step: " + str(step) + " =========================")
        res, time, cnt = root.update_network(nodes, time, cnt)
    
    # ノード平均深さと経路平均RSSIの出力
    ave_depth = np.mean([node.depth() for node in nodes[1:]])
    ave_rssi = np.mean([node.uplink_rssi() for node in nodes[1:]])
    ave_depths.append(ave_depth)
    ave_rssis.append(ave_rssi)
    print("No." + str(i) + ": ave_depth = " + str(ave_depth) + ", ave_rssi = " + str(ave_rssi))
    nio.update_graph(nodes, step, time, cnt, fig, ax, is_fixed_axis=True, is_save=True) # グラフの更新

    # ノード故障
    unable_node = random.choice(nodes[1:])  # 非ルートノードを1つ選択
    unable_node.disable(nodes)
    print("Node " + str(unable_node.id) + " is disabled.")
    nio.update_graph(nodes, step, time, cnt, fig, ax, is_fixed_axis=True) # グラフの更新

    # ネットワーク再構成
    # 現状手法
    if is_previous_rouing:
        root.init_network()
        res = 0
        while res != -1:
            step += 1
            print("\n========================= Step: " + str(step) + " =========================")
            res, time, cnt = root.update_network(nodes, time, cnt)
        
        time ,cnt = 0, 0    # 計測開始
        root.build_network()
        res = 0
        while res != -1:
            step += 1
            print("\n========================= Step: " + str(step) + " =========================")
            res, time, cnt = root.update_network(nodes, time, cnt)
        
    # 提案手法
    else:
        time ,cnt = 0, 0    # 計測開始
        res = 0
        while res != -1:
            step += 1
            print("\n========================= Step: " + str(step) + " =========================")
            res, time, cnt = root.update_network(nodes, time, cnt)

    # 復旧経過時間と復旧通信回数の出力
    times.append(time)
    cnts.append(cnt)
    print("No." + str(i) + ": time = " + str(time) + ", cnt = " + str(cnt))
    nio.update_graph(nodes, step, time, cnt, fig, ax, is_fixed_axis=True, is_save=True) # グラフの更新

    # ノード復帰
    enable_node = nm.search_node(nodes, unable_node.id)
    enable_node.enable()
    nio.update_graph(nodes, step, time, cnt, fig, ax, is_fixed_axis=True) # グラフの更新

    # ネットワーク初期化
    root.init_network()
    res = 0
    while res != -1:
        step += 1
        print("\n========================= Step: " + str(step) + " =========================")
        res, time, cnt = root.update_network(nodes, time, cnt)
    nio.update_graph(nodes, step, time, cnt, fig, ax, is_fixed_axis=True) # グラフの更新


# 結果の表示
if is_previous_rouing: 
    print("\\********** Previous Routing **********")
else:
    print("\\********** Proposed Routing **********")
print("[Result (" + str(NUM_OF_TRIAL) + "-trial average)]")
print("Average node depth: " + str(np.mean(ave_depths)))
print("Average route RSSI: " + str(np.mean(ave_rssis)) + "[dBm]")
print("Recovery elapsed time: " + str(np.mean(times)) + "[ms]")
print("Recovery com count: " + str(np.mean(cnts)))
wait_command(nodes, step, time, cnt, fig, ax)

# CSVファイルに結果を出力
result = [["ave_depth", "ave_rssi", "time", "cnt"]]
for i in range(NUM_OF_TRIAL):
    result.append([ave_depths[i], ave_rssis[i], times[i], cnts[i]])

if is_previous_rouing: 
    with open("Experiment/result_previous_routing.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(result)
else:
    with open("Experiment/result_proposed_routing.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(result)
print("Saved the result.")

print("Good bye!")