#################### network_io.py ####################
# Input/Output functions for LPWA network simulation
# Note: This program needs "network_mod.py"
# @created      2023-08-11
# @developer    226E0214 Seiya Kinoshita
# @affiliation  Tanaka Lab. Kyutech
#################### ############# ####################

import pprint
import networkx as nx
import matplotlib.pyplot as plt
import network_mod as nm

import time as ti
 
# グラフの初期化
def init_graph() -> tuple:
  plt.close("all")  # 既存のウィンドウを閉じる
  plt.ion()         # 対話モード(ユーザからのコマンドライン入力を受け付ける)

  # 図の書式設定
  plt.rcParams["font.family"] ="Arial"        # フォント
  plt.rcParams["xtick.direction"] = "in"      # x軸の目盛線を内向きに
  plt.rcParams["ytick.direction"] = "in"      # y軸の目盛線を内向きに
  plt.rcParams["xtick.major.width"] = 1.0     # x軸主目盛り線の線幅
  plt.rcParams["ytick.major.width"] = 1.0     # y軸主目盛り線の線幅
  plt.rcParams["font.size"] = 20              # フォントの大きさ
  plt.rcParams["axes.linewidth"] = 1.0        # 軸の線幅

  return plt.subplots()

# グラフの更新
def update_graph(nodes: list, step: int, time: int, cnt: int, fig, ax, is_fixed_axis = False, is_save = False) -> None:
  graph = nx.DiGraph()
  nodes_list = []
  edges_list = []
  pos = dict()

  for node in nodes:
    pos[node.id] = node.pos       # 座標情報

    # ルートノードの色設定
    if type(node) is nm.RootNode:
      # 送信待ちノードのとき
      if node.sending_pkt:
        nodes_list.append((node.id, {"color": "orange"}))
      # 送信済みノードのとき
      else:
        nodes_list.append((node.id, {"color": "c"}))
      continue
    
    # 正常ノード
    if node.is_alive:
      # 親が存在するノードのとき
      if node.candidate_tbl != []:
        edges_list.append((node.id, node.uplink_id(), {"color": "black"}))
        # 送信待ちノードのとき
        if node.sending_pkt:
          nodes_list.append((node.id, {"color": "orange"}))
        # 送信済みノードのとき
        else:
          nodes_list.append((node.id, {"color": "c"}))

      # 親が存在しないノードのとき
      else:
        # 送信待ちノードのとき
        if node.sending_pkt:
          nodes_list.append((node.id, {"color": "orange"}))
        else:
          nodes_list.append((node.id, {"color": "gold"}))

    # 故障ノード
    else:
      nodes_list.append((node.id, {"color": "lightgray"}))

  graph.add_nodes_from(nodes_list)      # グラフにノードを追加
  graph.add_edges_from(edges_list)      # グラフに辺を追加
  node_color = [node["color"] for node in graph.nodes.values()]   # ノードの色情報を格納
  edge_color = [edge["color"] for edge in graph.edges.values()]   # 辺の色情報を格納
  
  ax.clear()  # 描画領域の初期化

  # グラフの描画
  nx.draw(graph, pos=pos, with_labels=True, node_color=node_color,edge_color=edge_color, ax=ax)

  # 描画領域の書式設定
  ax.set_aspect("equal")
  ax.set_xlabel("x [km]", size=20, weight="light")
  ax.set_ylabel("y [km]", size=20, weight="light")
  ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
  ax.axis("on")
  # 座標軸の固定
  if is_fixed_axis:
    ax.set_xlim([-16,16])
    ax.set_ylim([-16,16])
    plt.xticks([-15.0, -7.5, 0.0, 7.5, 15.0])
    plt.yticks([-15.0, -7.5, 0.0, 7.5, 15.0])

  # 有効数字小数点第1位
  plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter("%.1f"))
  plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter("%.1f"))

  # 計測情報の表示
  ax.text(0.01, 1.01, "Step: " + str(step), transform=ax.transAxes)
  ax.text(0.5, 1.01, "Time: " + str(time) + "ms", ha="center", transform=ax.transAxes)
  ax.text(0.99, 1.01, "Count: "  + str(cnt), ha="right", transform=ax.transAxes)
  
  fig.canvas.draw()
  fig.canvas.flush_events()
  
  # グラフの保存
  if is_save: plt.savefig("Figures\\fig_" + str(step), bbox_inches="tight")
  
  return


# 受信パケットの出力
def print_received_packets(nodes: list) -> None:
  print()
  print("[Received packets]")
  for node in nodes:
    if not node.received_pkt: continue  # 受信パケットの無いノードは非表示
    print("#" + str(node.id) + ": " + str(node.received_pkt))
  print()
  return

# 送信パケットの出力
def print_sending_packets(nodes: list) -> None:
  print()
  print("[Sending packets]")
  for node in nodes:
    if not node.sending_pkt: continue   # 送信パケットの無いノードは非表示
    print("#" + str(node.id) + ": " + str(node.sending_pkt))
  print()
  return

# 経路候補表の出力
def print_candidate_tables(nodes: list) -> None:
  print()
  print("[Routing Candidate Table] (# Node ID: [{Candidate ID, Depth, RSSI, UplinkID}, ...])")
  for node in nodes:
    if node.candidate_tbl == []: continue # 経路情報の無いノードは非表示
    print("# " + str(node.id) + ":")
    pprint.pprint(node.candidate_tbl)
  print()
  return

# 子ノードリストの出力
def print_dnlink(nodes: list) -> None:
  print()
  print("[Downlink ID] (# Node ID: [Downlink ID])")
  for node in nodes:
    if not node.dnlink_ids: continue    # 子が存在しないノードは非表示
    print("# "  + str(node.id) + ": " + str(node.dnlink_ids))
  print()
  return

# 時系列やカウント情報の出力
def print_counts(nodes: list) -> None:
  print()
  print("[Clock, Step count of waiting to send and pause](# Node ID: [Clock, (Count of waiting, Count of pause)])")
  for node in nodes:
    print("#" + str(node.id) + ": [" + str(node.clock) + ", (" + str(node.waiting_time), ", " + str(node.pause_time) + ")]")
  print()
  return

# コマンドライン処理
def wait_command(nodes: list, step: int, time: int, cnt: int, fig, ax) -> tuple:
  
  while True:
    try:
      s = input("Input command (\"h\": help)>> ")
      
      # コマンドライン処理
      if not s:
        continue
      elif s == "h":
        print("\n[Commands]\n\
              h               : show help\n\
              n               : next process\n\
              f               : fast forward until all nodes are ready to send\n\
              e               : exit\n\
              i               : initialize network\n\
              b               : build network\n\
              a [id] [x] [y]  : add node [id] to position [x] [y]\n\
              m [id]          : enable nodes [id] ...\n\
              d [id]          : disable nodes [id] ...\n\
              r               : show routing candidate tables\n\
              s               : show downlink nodes\n\
              t               : show clock & waiting/pause time info of nodes\n\
              c               : clear time & communication count\n")
        
      elif s == "n":          # 処理を続行
        return True, False, False
      elif s == "f":          # # 全ノードが送信できる状態まで早送り
        return True, True, False
      elif s == "e":          # 終了
        return False, False, False
      
      elif s == "i":          # ネットワーク初期化命令
        nm.search_root_node(nodes).init_network()
        return True, False, False
      
      elif s == "b":          # ネットワーク構築命令
        nm.search_root_node(nodes).build_network()
        return True, False, False
      
      elif s[0] == "a":       # ノード追加
        c, id, x, y = s.split()
        if nm.search_node(nodes, id) is None:
          nodes.append(nm.Node(id, (int(x), int(y))))
          update_graph(nodes, step, time, cnt, fig, ax)
          continue
        else:
          print("Error: Node " + str(id) + " already exists")

      elif s[0] == "m":     # ノード有効化(正常状態)
        c, id = s.split()
        enable_node = nm.search_node(nodes, id)
        if enable_node is None:
          print("Error: Node " + str(id) + " does not exist")
        else:
          enable_node.enable()
        update_graph(nodes, step, time, cnt, fig, ax)
        continue
      
      elif s[0] == "d":     # ノード無効化(故障状態)
        c, id = s.split()
        unable_node = nm.search_node(nodes, id)
        if unable_node is None:
          print("Error: Node " + str(id) + " does not exist")
        else:
          unable_node.disable(nodes)
        update_graph(nodes, step, time, cnt, fig, ax)
        continue

      elif s[0] == "r":
        print_candidate_tables(nodes)
        continue
      elif s[0] == "s":
        print_dnlink(nodes)
        continue
      elif s[0] == "t":
        print_counts(nodes)
        continue
      elif s[0] == "c":     # 予想経過時間と通信回数の初期化
        print("Note: Cleared time and communication count.")
        return True, False, True
      else:
        print("Error: Incorrect command")
    
    # 例外処理
    except EOFError as e:
      print("Error: Incorrect command [" + str(e) + "]")
    except ValueError as e:
      print("Error: Incorrect command ["+ str(e) + "]")


if __name__ == "__main__":
  pass