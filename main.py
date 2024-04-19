############################## main.py ##############################
# Main file for LPWA network simulation
# Note: This program needs "network_mod.py" and "network_io.py"
# @created      2023-08-11
# @developer    226E0214 Seiya Kinoshita
# @affiliation  Tanaka Lab. Kyutech
############################## ####### ##############################

from network_mod import *
from network_io import *
import random

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
nio.update_graph(nodes, step, time, cnt, fig, ax)
is_executing, is_fast_forwarding, is_reset = wait_command(nodes, step, time, cnt, fig, ax)  # コマンド受付

# メインループ
while is_executing:

  # ネットワークの更新処理
  step += 1
  print("\n========================= Step: " + str(step) + " =========================")
  res, time, cnt = root.update_network(nodes, time, cnt)
  print("[Estimated elapsed time] : " + str(time) + "ms")
  print("[Communication count]    : " + str(cnt) + "\n")
  if res == -1:
    print("\n****** Network update has finished ******\n")
    is_fast_forwarding = False

  nio.update_graph(nodes, step, time, cnt, fig, ax) # グラフの更新
  
  # 早送り中でなければコマンド受付
  if not is_fast_forwarding:
    # nio.update_graph(nodes, step, time, cnt, fig, ax) # グラフの更新
    is_executing, is_fast_forwarding, is_reset = wait_command(nodes, step, time, cnt, fig, ax)
    # 計測情報の初期化
    if is_reset:
      time = 0
      cnt = 0
  
print("Good bye!")