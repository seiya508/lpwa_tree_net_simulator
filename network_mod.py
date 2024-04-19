#################### network_mod.py ####################
# Modules of nodes for LPWA network simulation
# Note: This program needs "settings.py" and "network_io.py"
# @created      2023-08-11
# @developer    226E0214 Seiya Kinoshita
# @affiliation  Tanaka Lab. Kyutech
#################### ############## ####################

import json
import random
import settings as st
import network_io as nio

# 送信済みノード履歴(時間測定で使用)
sent_nodes_history = []


###################################### ノードクラス #####################################
class Node:

  # 各ノードは以下の情報を記憶している
  def __init__(self, ID: int, POS: tuple) -> None:
    self.is_alive = True                  # 状態変数(True: 正常, False: 故障) 
    self.id = ID                          # 自ノードID
    self.pos = POS                        # 座標
    self.clock = 0                        # 論理時計
    self.sending_pkt = ""                 # 送信パケット
    self.received_pkt = ""                # 受信パケット
    self.waiting_time = 0                 # 送信待ち時間
    self.pause_time = st.SENDING_INTERVAL # 送信経過時間(初期値:通信可能な時間)
    self.candidate_tbl = []                 # 経路候補表
    self.dnlink_ids = set()               # 子ノードリスト(ID集合)
    return

  # 親ノードID
  def uplink_id(self) -> int:
    if self.candidate_tbl == []: return None
    return int(self.candidate_tbl[0]["candidate_id"])
  
  # 自ノード深さ
  def depth(self) -> int:
    if self.candidate_tbl == []: return st.DEPTH_LIM
    return int(self.candidate_tbl[0]["depth"] + 1)
  
  # 上方向経路RSSI
  def uplink_rssi(self) -> float:
    if self.candidate_tbl == []: return st.DEPTH_LIM
    return float(self.candidate_tbl[0]["rssi"])
  
  # Helloパケット発信
  def hello(self) -> None:

    if self.depth() >= st.DEPTH_LIM:       # 深さが上限を超えていたらスキップ
      print("Warning: Depth limit exceeded!")
      print("Is partial network completely isolated?")
      return

    self.sending_pkt = json.dumps({
          "type"      : 1,
          "clock"     : self.clock,
          "my_id"     : self.id,
          "uplink_id" : self.uplink_id(),
          "my_depth"  : self.depth(),
          })
    self.waiting_time = st.SENDING_TIME
    return
  
  # Byeパケット発信
  def bye(self) -> None:
    self.sending_pkt = json.dumps({"type": 2, "clock": self.clock, "my_id": self.id})
    self.waiting_time = st.SENDING_TIME
    return

  # Aloneパケット発信
  def alone(self) -> None:
    self.sending_pkt = json.dumps({"type": 3, "clock": self.clock, "my_id": self.id})
    self.waiting_time = st.SENDING_TIME
    return
  
  # 経路候補表の経路の探索
  # (引数)    探索する候補ノードID
  # (戻り値)  経路の順位, -1: 該当経路なし
  def search_route(self, id: int) -> int:
    for i, route in enumerate(self.candidate_tbl):
      if int(id) == int(route["candidate_id"]): return i
    return -1
  
  # 経路候補表の経路の削除
  # (引数) 経路候補表, 削除するバックアップノードのID
  # (戻り値)
  # 1:  親ノード(0番要素)の削除
  # 0:  削除
  # -1: 該当経路なし
  def remove_route(self, id: int) -> int:
    for i, route in enumerate(self.candidate_tbl):
      if int(id) == int(route["candidate_id"]):
        del self.candidate_tbl[i]
        return int(i == 0)
    return -1

  # [※]経路候補表への対象経路の挿入・更新処理
  # 経路制御アルゴリズムに従う
  # (引数) 新しい経路
  # (戻り値)
  # 1:  親ノード(0番要素)の更新
  # 0:  バックアップ(1番以降)ノードの更新
  # -1: 既存の経路候補表に追加
  def update_route(self, new_route: dict) -> int:

    # (1) 経路候補表に経路情報が無いとき，対象経路を追加して終了
    if self.candidate_tbl == []:
      self.candidate_tbl.append(new_route)
      return 1
     
    # (2) 経路候補表に経路情報が存在するとき，経路候補表に送信ノードの経路が存在すれば，
    #     該当経路を削除して，経路候補表の0番要素から参照する
    else:
      # (2*) 以前のアルゴリズムを検証する場合：
      #      経路候補表に経路情報が既にあるとき，何もせず終了
      if st.is_previous_rouing: return 0
      
      res = (self.remove_route(new_route["candidate_id"]) == 1)
      for i, route in enumerate(self.candidate_tbl):
        
        # (2-1) 対象経路の深さが参照経路の深さより小さいとき，その直前に挿入して終了
        if new_route["depth"] < route["depth"]:
          self.candidate_tbl.insert(i, new_route)
          return int(res or int(i == 0))
        
        # (2-2) 対象経路の深さが参照経路の深さと等しく，対象経路の電波強度が参照経路の電波強度より大きいとき，その直前に挿入して終了
        #       そうでない場合，経路候補表の次の要素を参照して(2-1)から続行
        elif new_route["depth"] == route["depth"] and new_route["rssi"] > route["rssi"]:
          self.candidate_tbl.insert(i, new_route)
          return int(res or int(i == 0))
        
      # (3) 経路候補表末尾に対象経路を追加して終了
      self.candidate_tbl.append(new_route)
      return int(res) if res else -1
  
  # 初期化
  def clear(self) -> None:
    self.clock = 0
    self.sending_pkt = ""
    self.received_pkt = ""
    self.waiting_time = 0
    self.pause_time = st.SENDING_INTERVAL
    self.candidate_tbl.clear()
    self.dnlink_ids.clear()
    return

  # 周囲ノードへのブロードキャスト
  # (引数) ノードリスト
  # (戻り値)
  #  0: ブロードキャストに成功
  # -1: エラー(送信パケット無しor送信休止中)
  def broadcast(self, nodes: list) -> int:
    if not self.sending_pkt: return -1                  # 送信パケットが無いときはスキップ
    if self.pause_time < st.SENDING_INTERVAL: return -1 # 送信休止中のときはスキップ
    for node in nodes:
      if node is self or not node.is_alive: continue    # 故障ノードはスキップ

      # 送信パケットにRSSIを付加(実際のネットワークではこの計算は行わない)
      rssi = st.calc_rssi(self.pos, node.pos)
      if rssi < st.RSSI_LWLIM : continue                # RSSIが下限値を下回ったらスキップ
      node.received_pkt = self.sending_pkt[:-1] + ", \"rssi\": "+ str(rssi) +"}"

    self.sending_pkt = ""   # 送信パケットの初期化
    self.waiting_time = 0   # 送信待ち時間の初期化
    self.pause_time = 0     # 送信経過時間の初期化
    return 0


  # 受信パケットからノードの各情報を更新
  # (戻り値)
  #  1: 送信パケットを作成して終了
  #  0: 送信パケットを作成せず終了
  # -1: エラー(受信パケット無し)
  def update(self) -> int:
    
    if not self.received_pkt: return -1         # 受信パケットが無いときはスキップ
    items = json.loads(self.received_pkt)       # 受信パケットから必要な要素を取り出す
    self.received_pkt = ""                      # 受信パケットを初期化
    if not self.is_alive: return -1             # 故障ノードはスキップ

    # Helloパケット受信
    if items.get("type") == 1:
      if items.get("clock") < self.clock: return 0    # 過去のパケットはスキップ
      self.clock = items.get("clock")                 # 論理時計の更新
        
      is_changed_parent = False   # 親ノード更新フラグ
      new_route = {
        "candidate_id": items.get("my_id"),
        "uplink_id"   : items.get("uplink_id"),
        "depth"       : items.get("my_depth"),
        "rssi"        : items.get("rssi")
        }

      # (1) 送信ノードの親が自ノードのとき，子ノードリストに送信ノードIDを追加し，
      #     経路候補表に送信ノードの経路が存在すれば，該当経路を削除
      #     このとき，経路候補表に経路情報が存在しなくなったら終了
      if items.get("uplink_id") == self.id:
        self.dnlink_ids.add(items.get("my_id"))
        is_changed_parent = (self.remove_route(items.get("my_id")) == 1)
        if self.candidate_tbl == []: return 0
      
      # (2) 送信ノードの親が自ノード以外のとき
      # (2-1) 子ノードリストに送信ノードIDが含まれているとき
      # 子ノードリストから送信ノードIDを削除，経路候補表に送信ノードの経路を挿入・更新処理[※]
      elif items.get("my_id") in self.dnlink_ids:
        self.dnlink_ids.remove(items.get("my_id"))
        is_changed_parent = (self.update_route(new_route) == 1)

      # (2-2) 子ノードリストに送信ノードIDが含まれていないとき，経路候補表に送信ノードの経路を挿入・更新[※]
      else:
        is_changed_parent = (self.update_route(new_route) == 1)

      # (3) (2-1), (2-2)において親ノード(0番要素)が更新されたとき，自ノード情報に書き換えたHelloパケットを中継
      if is_changed_parent:
        self.hello()
        return 1
      return 0
    
    # Byeパケット受信
    elif items.get("type") == 2:
      if items.get("clock") < self.clock : return 0   # 過去のパケットはスキップ
      elif items.get("clock") == self.clock:
        if items.get("my_id") in self.dnlink_ids:     # 子ノードIDの削除
          self.dnlink_ids.remove(items.get("my_id"))
        return 0
      if self.candidate_tbl == []: return 0             # 初期化済みのときはスキップ
      
      self.candidate_tbl.clear()
      self.clock = items.get("clock")                 # 論理時計の更新
      
      # Byeパケットの中継
      self.bye()
      return 1
    
    # Aloneパケット受信
    # 今回論理時計clockは考慮しない
    elif items.get("type") == 3:
      if items.get("my_id") == self.uplink_id():
        self.remove_route(items.get("my_id"))
        if self.candidate_tbl != []: self.hello() # Helloパケット発信
        else: self.alone()                      # Aloneパケット中継
        return 1
    return 0
  
  # ノード復帰
  def enable(self) -> None:
    self.is_alive = True
    return

  # ノード故障
  def disable(self, nodes: list) -> None:
    self.is_alive = False

    if not st.is_previous_rouing:
      # 経路候補表の停止ノードの経路を削除(実際は周囲ノードが異常を検知して自ら削除)
      for node in nodes:
        if type(node) is RootNode: continue
        if not node.is_alive: continue
        if node.remove_route(self.id) == 1:

          # ネットワーク孤立判定
          if node.candidate_tbl == []:
            print("Warning: Node " + str(node.id) + " may be alone.")
            # 子ノードがいるときは，子ノードに新しい親を探させる
            if node.dnlink_ids != []: node.alone()  # Aloneパケット発信
          else: node.hello()                        # Helloパケット発信

      # 親ノードの子ノード情報を削除
      if self.uplink_id() != None:
        uplink_node = search_node(nodes, self.uplink_id())
        uplink_node.dnlink_ids.remove(self.id)
    
    self.clear()  # 故障ノードを初期化
    return

######################################## ノードクラス終 #######################################


###################################### ルートノードクラス #####################################
class RootNode(Node): # ノードクラスを継承

  def uplink_id(self) -> int:
    return 0
  
  def depth(self) -> int:
    return 0
  
  def hello(self) -> None:
    self.sending_pkt = json.dumps({
    "type"      : 1,
    "clock"     : self.clock,
    "my_id"     : self.id,
    "uplink_id" : 0,
    "my_depth"  : 0,
    })
    self.waiting_time = st.SENDING_TIME
    return

  def broadcast(self, nodes: list) -> int:
    if not self.sending_pkt: return -1                  # 送信パケットが無いときはスキップ
    if self.pause_time < st.SENDING_INTERVAL: return -1 # 送信休止中のときはスキップ
    for node in nodes:
      if node is self or not node.is_alive: continue    # 故障ノードはスキップ

      # 送信パケットにRSSIを付加(実際のネットワークではこの計算は行わない)
      rssi = st.calc_rssi(self.pos, node.pos)
      if rssi < st.RSSI_LWLIM : continue                # RSSIが下限値を下回ったらスキップ
      node.received_pkt = self.sending_pkt[:-1] + ", \"rssi\": "+ str(rssi) +"}"

    self.sending_pkt = ""   # 送信パケットの初期化
    self.waiting_time = 0   # 送信待ち時間の初期化
    self.pause_time = 0     # 送信経過時間の初期化

    print("Note: Root node sent a packet!")
    return 0

  def update(self) -> int:
    if not self.received_pkt: return -1         # 受信パケットが無いときはスキップ
    items = json.loads(self.received_pkt)       # 受信パケットから必要な要素を取り出す
    self.received_pkt = ""                      # 受信パケットを初期化

    # Helloパケットを受信したときは子ノード情報を更新
    if items.get("type") == 1:
      if items.get("uplink_id") == self.id:
        self.dnlink_ids.add(items.get("my_id"))

    # Byeパケットを受信したときは子ノード情報を削除
    elif items.get("type") == 2:
      if items.get("my_id") in self.dnlink_ids:
        self.dnlink_ids.remove(items.get("my_id"))

    return 0

  # Helloパケット発信
  def build_network(self) -> None:
    if self.pause_time < st.SENDING_INTERVAL: # 送信休止中のとき
      print("Note: Root node is pausing. Pause time: " + str(self.pause_time))
    if self.clock % 2 == 0:                   # ネットワークの状態を論理時計でチェック
      self.clock += 1
      self.hello()
    else:
      print("Note: Hello packet has already sent!")
    return
  
  # Byeパケット発信
  def init_network(self) -> None:
    if self.pause_time < st.SENDING_INTERVAL: # 送信休止中のとき
      print("Note: Root node is pausing. Count of pause: " + str(self.pause_time))
    if self.clock % 2 == 1:                   # ネットワークの状態を論理時計でチェック
      self.clock += 1
      self.bye()
    else:
      print("Note: Bye packet has already sent!")
    return

  # ネットワーク更新処理
  # (ルートノードの探索を減らすためにクラスメソッドで定義)
  # (引数) ノードリスト
  # (戻り値)
  #  0: 送信ノードの1つを処理
  # -1: 更新終了
  def update_network(self, nodes: list, time: int, cnt: int) -> tuple:
    
    # 送信待ちノードの存在判定
    for i, node in enumerate(nodes):
      if node.is_alive and node.sending_pkt: break
      # 送信待ちノードがいないとき
      if i == len(nodes)-1:
        # さらに送信休止中のノード判定
        for node in nodes:
          # 送信待ちノードは無いが，送信休止中のノードがあるときは時間を加算してスキップ
          if node.pause_time < st.SENDING_INTERVAL:
            print("Note: There are the pausing nodes.")
            time += st.SENDING_TIME
            sent_nodes_history.clear()
            for node in nodes:
              if node.is_alive: node.pause_time += st.SENDING_TIME
            return 0, time, cnt
        return -1, time, cnt  # すべてのノードが送信可能になってネットワークの処理が終了

    # 送信待ちノードをランダムに選択してブロードキャスト
    # 重みを付けてランダムに選ばせる
    weights = [
      (
        node.waiting_time                           # 受信順
        * (node.is_alive)                           # 正常ノード判定
        * (node.pause_time >= st.SENDING_INTERVAL)  # 送信休止中ノード判定
       )
      for node in nodes
      ]
    
    # 送信できる送信待ちノードがいない(重みがすべて0)ときは時間を加算してスキップ
    if sum(weights) == 0:
      print("Note: There are pausing nodes, which have a sending packet.")
      time += st.SENDING_TIME
      sent_nodes_history.clear()

      # 送信経過時間，送信待ち時間の加算
      for node in nodes:
        if node.is_alive:
          node.pause_time += st.SENDING_TIME
          if node.sending_pkt:
            node.waiting_time += st.SENDING_TIME
      return 0, time, cnt
    
    sending_node = random.choices(nodes, weights=weights)[0]
    sending_node.broadcast(nodes)
    cnt += 1
    nio.print_received_packets(nodes)  # 受信パケットの確認
    
    # 経過時間の計算と時間の更新
    is_time_elapsed = False
    for sent_node in sent_nodes_history:
      if st.calc_rssi(sending_node.pos, sent_node.pos) >= st.RSSI_LWLIM:
        time += st.SENDING_TIME
        sent_nodes_history.clear()
        is_time_elapsed = True
        
    sent_nodes_history.append(sending_node)
    
    for node in nodes:
      if node.is_alive:
        if is_time_elapsed:                     # 時間経過を検知したら
          node.pause_time += st.SENDING_TIME    # 送信経過時間の加算
          if node.sending_pkt:                  # 送信待ちのときは送信待ち時間を加算
            node.waiting_time += st.SENDING_TIME
      node.update()   # 各ノードが受信パケットを確認して送信パケットを作成
                
    nio.print_sending_packets(nodes)   # 送信パケットの確認

    return 0, time, cnt

  # ノード無効化
  def disable(self, nodes: list) -> None:
    print("Error: Root node cannot be disabled")
    return
#################################### ルートノードクラス終 ###################################

#################### 予備関数 ####################
# ノード探索
# (引数)    ノードリスト, ノードID 
# (戻り値)  ノードオブジェクト
def search_node(nodes: list, id: int) -> Node:
  for node in nodes:
    if int(id) == int(node.id): return node
  return None

# ルートノード探索
# (引数)    ノードリスト
# (戻り値)  ルートノードオブジェクト
def search_root_node(nodes: list) -> RootNode:
  for node in nodes:
    if type(node) is RootNode: return node
  return None
##################################################

if __name__ == '__main__':
  pass