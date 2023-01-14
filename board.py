import numpy as np
from enum import Enum

# 赤黄緑青紫/おじゃま
class Puyo(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2
    BLUE = 3
    PURPLE = 4
    NUISANCE = 5


# クラスタ(隣接した4つ以上の同色ぷよ)
# puyo: 赤黄緑青紫
# indices: クラスタの要素の座標
# nuisances: クラスタに隣接するおじゃまぷよの座標
class Cluster:
    def __init__(self, _puyo, _indices, _nuisances):
        self.puyo = _puyo
        self.indices = _indices
        self.nuisances = _nuisances

    def __len__(self):
        return len(self.indices)


# 盤面
# field: ぷよのリスト
# 盤面に対する各種操作をここに加える
class Board:
    def __init__(self, _field):
        self.field = _field

    def __str__(self):
        return '\n'.join(' '.join('🔴🟡🟢🟦🟪🤍'[puyo.value] if puyo else '　' for puyo in hor) for hor in self.field[::-1])
    
    def find_clusters_fr(self):#ぷよを設置したときに連結数が4以上となる座標を探索する ※設置するぷよは1つのみ
        coordinates = []  # 座標のリスト

        # (y, x) を始点としたクラスタが存在すればリストに追加する
        def search_from_fr(y, x):
            start = (y, x)

            # (_y, _x) の上下左右に対して indicesを更新する
            def search_around(_y, _x):
                next_points = ((_y, _x - 1), (_y, _x + 1), (_y - 1, _x), (_y + 1, _x))
                for next in next_points:
                    __y, __x = next
                    if 0 <= __x < 6 and 0 <= __y < 12:
                        if next not in indices and self.field[next] == puyo_initial:
                            indices.append(next)
                            search_around(*next)

            for next in ((y + 1, x - 1), (y + 1, x + 1),(y, x - 1), (y, x + 1), (y - 1, x)):#自身を隣接するぷよと同じ色にして探索する
                _y, _x = next
                if 0 <= _x < 6 and 0 <= _y < 12:
                    if self.field[next] and self.field[next] != Puyo.NUISANCE:
                        puyo_initial = self.field[next]
                        indices = [start]
                        search_around(*start)

                        if len(indices) >= 4:  # 大きさが4以上なら色と座標を追加
                            coordinates.append((puyo_initial,(_y,x)))

        for x in range(0, 6):
            y = len(self.field[:, x][self.field[:, x] != [None]])
            search_from_fr(y, x)

        return set(coordinates)

    def append_puyo(self, i):
        clusters = self.find_clusters_fr()
        color, (y, x) = clusters[i]
        self.field[y][x] = color

    def find_clusters(self):
        clusters = []  # クラスタのリスト
        seen = []  # すでに辿った座標

        # (y, x) を始点としたクラスタが存在すればリストに追加する
        def search_from(y, x):
            start = (y, x)

            puyo_initial = self.field[start]
            indices = [start]
            nuisances = []

            # (_y, _x) の上下左右に対して indices, nuisances を更新する
            def search_around(_y, _x):
                next_points = ((_y, _x - 1), (_y, _x + 1), (_y - 1, _x), (_y + 1, _x))
                for next in next_points:
                    __y, __x = next
                    if 0 <= __x < 6 and 0 <= __y < 12:
                        if next not in indices and self.field[next] == puyo_initial:
                            indices.append(next)
                            search_around(*next)
                        if next not in nuisances and self.field[next] == Puyo.NUISANCE:
                            nuisances.append(next)

            search_around(*start)
            seen.extend(indices)

            if len(indices) >= 4:  # 大きさが4以上ならクラスタをリストに追加
                clusters.append(Cluster(puyo_initial, indices, nuisances))

        for y in range(0, 12):
            if all(puyo is None for puyo in self.field[y]):  # y行目がすべて背景なら
                break
            for x in range(0, 6):
                if (y, x) not in seen:  # 未探索なら
                    puyo = self.field[y, x]
                    if puyo and puyo != Puyo.NUISANCE:  # 背景やおじゃまぷよでなければ
                        search_from(y, x)

        return clusters

    # クラスタを構成しているぷよを消す
    # 消したクラスタを返す
    def pop_clusters(self):
        clusters = self.find_clusters()
        for c in clusters:
            print(vars(c))
            for y, x in c.indices:
                self.field[y, x] = None
            for y, x in c.nuisances:
                self.field[y, x] = None
        return clusters

    # 浮いているぷよを落とす
    def drop_puyo(self):
        for i in range(0, 6):
            column = self.field[:, i][self.field[:, i] != [None]]  # None を除いた i 列目
            n = len(column)
            self.field[:n, i] = column  # i 列目の n 行目までを column で置き換え
            self.field[n:, i] = None  # i 列目の n 行目からを 削除


            


# 連鎖をシミュレーションして得点を返す. 現在落下ボーナスは考慮していない
def simulate(board):
    # 色/連結/連鎖ボーナス
    class Bonus:
        color = [0, 0, 3, 6, 12, 24]
        size = [0, 0, 0, 0, 0, 2, 3, 4, 5, 6, 7, 10]
        chain = [0, 0, 8, 16, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 480, 512]
        zenkeshi = [0, 3500]

    point, chain = 0, 1
    zenkeshi = True #仮の値　
    while True:
        print()
        print(board)
        clusters = board.pop_clusters()
        if not clusters:  # 連鎖終了なら得点を返す
            if zenkeshi: #連鎖開始時に全消しだった場合
                point += 3500
                print("全消しボーナス:+3500点")
                print(f'計{point}点')
            
            zenkeshi = not any(board.field[0])#field最下段が空なら全消しをTrueにする
            if zenkeshi:
                print(f"全消し:{zenkeshi}")
            return point

        puyos = sum(len(c) for c in clusters)  # 消えた数
        colors = len({c.puyo.value for c in clusters})  # 消えた色数
        bonus_size = sum(Bonus.size[min(len(c), 11)] for c in clusters)  # 連結ボーナス
        point += max(puyos * (Bonus.color[colors] + bonus_size + Bonus.chain[chain]) * 10, 40)
        print(f'{chain}連鎖目:', f'計{point}点')
        board.drop_puyo()
        chain += 1

    

def find_template():
    template = {
        "GTR" : [[(0,0),(0,1),(1,2),(2,1)], [(1,0),(1,1),(2,0)]],
        "新GTR": [[(0,0),(0,1),(0,2),(1,3),(2,2)],[(1,0),(1,1),(1,2)]],
        "不機嫌GTR":[[(0,0),(1,1),(1,2)],[(0,1),(0,2),(1,3),(2,2)]],
        "だぁ積み":[[(0,0),(1,0),(1,1)],[(0,1),(0,2),(1,2)]],
        "211鍵": [[(0,0),(1,0),(2,1)],[(0,1),(1,1),(2,2),(3,1)]],
        "121鍵": [[(0,0),(1,1),(2,1)],[(0,1),(1,2),(2,2),(3,1)]],
        "31階段":[[(0,1),(1,1),(2,1)],[(0,2),(1,2),(2,2),(1,3)]],
        "サブマリン": [[(0,0),(0,1),(1,0)],[(0,2),(0,3),(1,1),(1,3)]],
        "ペルシャ式": [[(0,0),(0,1),(0,2)],[(0,3),(0,4),(0,5),(1,2)],[(1,1),(1,4),(2,3),(2,4)]],
        "fron積み": [[(0,0),(0,1),(0,3),(2,2)],[(0,2),(1,1),(1,2)]],
        "LLR": [[(0,0),(0,1),(2,2)],[(0,2),(2,1),(1,2)],[(1,0),(1,1),(2,1)]],
        "弥生時代": [[(0,0),(0,1),(0,2)],[(0,3),(0,4),(0,5)],[(1,0),(1,1),(1,2)],[(1,3),(1,4),(1,5)]]
        }
    for name, t in template.items():#templateに登録した座標の色が同じなら名前を返す
        if all([len({board.field[y][x] for y,x in c})==1 for c in t]):
            return name
    return "else"#どれにも当てはまらなかったとき




# 使用例
field = np.random.choice(list(Puyo), 78).reshape(13, 6)[::-1]
#検証用
field = np.array([[None] * 6 for i in range(13)])
field[3]  = [Puyo.RED,None,None,None,Puyo.RED,Puyo.NUISANCE]
field[2]  = [Puyo.RED,Puyo.BLUE,Puyo.BLUE,Puyo.RED,Puyo.GREEN,Puyo.RED]
field[1] = [Puyo.RED,Puyo.RED,Puyo.GREEN,Puyo.BLUE,Puyo.BLUE,Puyo.RED]
field[0] = [Puyo.GREEN,Puyo.GREEN,Puyo.BLUE,Puyo.GREEN,Puyo.GREEN,Puyo.GREEN]

board = Board(field)
print(find_template())
#print(Board.find_clusters_fr(board))
simulate(board)



