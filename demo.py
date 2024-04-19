############################## demo.py ##############################
# Demonstration file for LPWA network simulation
# Note: This program needs "network_mod.py" and "network_io.py"
# @created      2023-12-26
# @developer    226E0214 Seiya Kinoshita
# @affiliation  Tanaka Lab. Kyutech
############################## ####### ##############################

from network_mod import *
from network_io import *

root = RootNode(0, (0, 0))   # ルートノード

nodes = [
    root,   # ルートノードを1つだけ必ず含める

    Node(1, (-2, -3)),     Node(2, (-2, -5)),     Node(3, (2, -4)),
    Node(4, (2, -6)), Node(5, (1, -9))
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