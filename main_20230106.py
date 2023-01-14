import cv2
import numpy
import json
import math
from collections import deque
from yt_dlp import YoutubeDL
import os
import openpyxl

#前回からの変更点
#url.xlsx から動画をDL , 盤面取得ののち削除するようにした
#url.xlsx のD列に表記ぶれがあったため、"〇〇 vs ××"の形に整形した。
#↑ jsonにはプレイヤー名を記録しているため、必ず整形してから実行すること
#次のgameに移行したと判定する条件に盤面が空であることを追加(条件が強すぎる？要検証)
#盤面の片方がほとんど検出できない動画がいくつか存在することに注意 


#fieldが正しくとれているか判定する
def check_field():
    try:#7500tick目でエラーが起きるため.
        x, y, w, h = cv2.boundingRect(frames[0])
        s, t, u, v = cv2.boundingRect(frames[1])     
        
        #フィールドの基準
        field_width = 268
        field_height = 482

        if abs(w - field_width) < 10 and abs(h - field_height) < 10 and abs(u - field_width) < 10 and abs(v - field_height) < 10:
            return True
        else:
            return False
    except:
        return False


#×を検出する
def check_score():
    # 検索対象画像とテンプレート画像の読み込み
    template = cv2.imread('score_template.png')

    x, y, w, h = cv2.boundingRect(frames[0])
    s, t, u, v = cv2.boundingRect(frames[1])

    # 画像の検索（Template Matching）
    result_p1 = cv2.matchTemplate(image[y+ int(h/48*49): y + int(h/96*103), x + int(w/48*29): x + int(w/24*17)], template, cv2.TM_CCORR_NORMED)
    # 相手の盤面
    result_p2 = cv2.matchTemplate(image[y+ int(h/48*49): y + int(h/96*103), s + int(u/12*5): s + int(u/2)], template, cv2.TM_CCORR_NORMED)
    
    # 検索結果の信頼度と位置座標の取得
    #1p側
    min_val, max_val_p1, min_loc, max_loc = cv2.minMaxLoc(result_p1)
    #2p側
    min_val, max_val_p2, min_loc, max_loc = cv2.minMaxLoc(result_p2)
    
    #連鎖が起きたか判定
    return max_val_p1 ** 2 > 0.84, max_val_p2 ** 2 > 0.85


#nextが動いたかどうか判定する
main_avg = [None,None]
right_avg = [None, None]
left_avg = [None, None]
main_Que = [deque([0]), deque([0])]
right_Que = [deque([0]), deque([0])]
left_Que = [deque([0]), deque([0])]

def check_next(i):#iはp1,p2に対応
    
    # 白黒の割合計算
    def right_calc_black_whiteArea(bw_image): #right
        image_size = bw_image.size
        whitePixels = cv2.countNonZero(bw_image)    
        whiteAreaRatio = (whitePixels/image_size)*100#[%]

        right_Que[i].append(whiteAreaRatio)
        #print(right_Que[i])
        global right_jud
        right_jud = False
        #print("rQ", right_Que[i], "wAR", whiteAreaRatio)
        if ((right_Que[i].popleft()<10) and (whiteAreaRatio>10)):
            right_jud = True

    def left_calc_black_whiteArea(bw_image): #left
        image_size = bw_image.size
        whitePixels = cv2.countNonZero(bw_image)
    
        whiteAreaRatio = (whitePixels/image_size)*100#[%]

        left_Que[i].append(whiteAreaRatio)
        #print(left_Que[i])
        global left_jud
        left_jud = False
        #print("lQ", left_Que[i], "wAR", whiteAreaRatio)
        if ((left_Que[i].popleft()<10) and (whiteAreaRatio>10)):
            left_jud = True


    def main_calc_black_whiteArea(bw_image): #main
        image_size = bw_image.size
        whitePixels = cv2.countNonZero(bw_image)
    
        whiteAreaRatio = (whitePixels/image_size)*100#[%]

        #print("White Area [%] : ", whiteAreaRatio)
        main_Que[i].append(whiteAreaRatio)
        #print("mQ", main_Que[i], "wAR", whiteAreaRatio)
        if ((main_Que[i].popleft()<10) and (whiteAreaRatio>10) and (right_jud) and (left_jud)):
            return True
        return False


    # グレースケールに変換
        #[p1,p2]
    main_gray = [gray_image[100:270, 490:570], gray_image[100:270, 740:830]][i]
    right_gray = [gray_image[100:270, 460:530], gray_image[200:270, 680:750]][i]
    left_gray = [gray_image[200:270, 530:600], gray_image[100:270, 780:850]][i]
    
    

    global main_avg 
    global right_avg 
    global left_avg

    # 比較用のフレームを取得する
    if main_avg[i] is None: #main
        main_avg[i] = main_gray.copy().astype("float")
    if right_avg[i] is None: #right
        right_avg[i] = right_gray.copy().astype("float")
    if left_avg[i] is None: #left
        left_avg[i] = left_gray.copy().astype("float")

    # 現在のフレームと移動平均との差を計算
    cv2.accumulateWeighted(main_gray, main_avg[i], 0.6) #main
    main_frameDelta = cv2.absdiff(main_gray, cv2.convertScaleAbs(main_avg[i]))
    cv2.accumulateWeighted(right_gray, right_avg[i], 0.6) #right
    right_frameDelta = cv2.absdiff(right_gray, cv2.convertScaleAbs(right_avg[i]))
    cv2.accumulateWeighted(left_gray, left_avg[i], 0.6) #left
    left_frameDelta = cv2.absdiff(left_gray, cv2.convertScaleAbs(left_avg[i]))

    # デルタ画像を閾値処理を行う
    right_thresh = cv2.threshold(right_frameDelta, 3, 255, cv2.THRESH_BINARY)[1] #right
    right_calc_black_whiteArea(right_thresh)
    left_thresh = cv2.threshold(left_frameDelta, 3, 255, cv2.THRESH_BINARY)[1] #left
    left_calc_black_whiteArea(left_thresh)
    main_thresh = cv2.threshold(main_frameDelta, 3, 255, cv2.THRESH_BINARY)[1] #main
    cv2.waitKey(30)
    return main_calc_black_whiteArea(main_thresh)

def get_field(image, frame):

    # bgr を hsv に変換して返す
    # ただし h ≦ 360, s, v < 256
    def get_hsv_from(bgr):
        b, g, r = (int(_) for _ in bgr)
        mi, ma = min(b, g, r), max(b, g, r)

        def h():
            if b == g == r:
                return 0
            if r == ma:
                return 60 * (g - b) / (ma - mi)
            if g == ma:
                return 60 * (b - r) / (ma - mi) + 120
            else:
                return 60 * (r - g) / (ma - mi) + 240

        H = int(h())
        S = int(255 * (ma - mi) / ma)
        V = int(ma)
        return H if H >= 0 else H + 360, S, V
    # hsv上のユークリッド距離を返す
    def distance_on_hsv(hsv0, hsv1):
        h0, s0, v0 = hsv0
        h1, s1, v1 = hsv1
        dh, ds, dv, = h0 - h1, s0 - s1, v0 - v1
        return math.sqrt(dh ** 2 + ds ** 2 + dv ** 2)

    # 赤黄緑青紫 + おじゃま
    puyo_HSV = [(354, 149, 167), (32, 84, 225), (117, 139, 200), (225, 114, 200), (277, 146, 192), (249, 4, 179)]

    # セル(A, B)の中点近点からHSVの平均値を取り、色を判定して返す
    def get_color_from(a, b):
        (ax, ay), (bx, by) = a, b
        dx, dy = (bx - ax) // 3, (by - ay) // 3
        mean = numpy.array([image[j, i] for i in range(ax + dx, bx - dx) for j in range(ay + dy, by - dy)]).mean(0)
        hsv = get_hsv_from(mean)
        dist = [distance_on_hsv(hsv, puyo_hsv) for puyo_hsv in puyo_HSV]
        min_index = int(numpy.argmin(dist))
        if dist[min_index] < 55:
            return min_index
        return None

    field = []
    x, y, w, h = cv2.boundingRect(frame)
    # (x, y) が フレームの左上頂点
    # (x + w, y + h) が フレームの右下頂点
    # つまり、最も左上のセルは ((x, y), (x + (w / 6), y + (h / 12)))
    # 同様に、最も右下のセルは (((x + (5w / 6), y + (11h / 12)), x + w, y + h)
    w //= 6
    h //= 12

    # points: セルの頂点となる点集合
    points = [[(x + (i * w), y + (j * h)) for i in range(0, 7)] for j in range(0, 13)]
    for i in range(0, 12):
        row = []
        for j in range(0, 6):
            # points[i][j] が セルの左上頂点
            # points[i + 1][j + 1] が セルの右下頂点
            row.append(get_color_from(points[i][j], points[i + 1][j + 1]))
        field.append(row)
    return field

#url.xlsx からプレイヤー名とurlを取得する
wb = openpyxl.load_workbook('URL.xlsx')
sheet = wb['Sheet1']
players = [v[0].value.split()[::2] for v in sheet['D2':"D318"]]
urls = [url[0].value for url in sheet["E2": "E318"]]
ids = [row[0].value + str(row[2].value).zfill(2) for row in sheet["A2": "C318"]]

for n in range(13,319):#12,14なら12列から13列まで取得する
    ydl_opts = {'format': 'bestvideo', 'outtmpl': ids[n - 2] + '.webm'}
    #urlから動画をDLする
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([urls[n - 2]])

    video = cv2.VideoCapture(ids[n - 2] +'.webm')
    tick = 0
    skip1, skip2 = False, False #連続して盤面を取得しないようフラグを作る
    tick1, tick2 = 0, 0
    game_no = 0
    frame_count = 0
    check_s = (False, False)
    check_n = (False, False)
    dict = {"compe_id":ids[n - 2], "players": [players[n - 2]],
            "games":[]}#gamesに各gameの情報を追加していく
    field_dict = {"game_no": game_no, "fields":[[],[]]} #1gameの各fieldを記録する

    while video.isOpened():
        ret, image = video.read()
        if not ret:
            break

        image = cv2.resize(image, (1280, 720))
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        _, thresh_binary = cv2.threshold(gray_image, 80, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh_binary, 1, 2)
        contours = [cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True) for cnt in contours]
        frames = sorted(contours, key=lambda cnt: cv2.contourArea(cnt))[-3:][:2]
        frames.sort(key=lambda cnt: cv2.boundingRect(cnt)[0])

        #field, ぷよが設置されているか確認
        if check_field():
            #fieldが95tick連続で検出できず、検知時のfieldが空なら次の試合に移動したと判断する
            if frame_count >= 95:
                
                #盤面最下段が[None]*6なら空であるとする
                if get_field(image, frames[0])[11].count(None) == 6 or get_field(image, frames[1])[11].count(None) == 6: 
                    if len(field_dict["fields"][0]) == 0 and len(field_dict["fields"][1]) == 0:#どちらも空ならゲームは行われていないため記録は不要
                        frame_count = 0
                        continue
                    # 片方の盤面取得ができていない場合に注意
                    print(field_dict)
                    dict["games"].append(field_dict)
                    game_no += 1
                    field_dict = {"game_no": game_no, "fields":[[],[]]}
                    skip1, skip2 = False, False
                    print("----next game----")

        else:#fieldの検出ができなかったら次のtickへ
            frame_count += 1 
            tick += 1
            continue

        frame_count = 0
        check_s = check_score()
        check_n = (check_next(0), check_next(1))
        
        if (check_s[0] or check_n[0]) and not skip1 and tick1 < tick:
            field = get_field(image, frames[0])# 自分の盤面
            field_dict["fields"][0].append({"tick":tick, "rensa": check_s[0],"field":field})#rensaがTrue→連鎖で取得した
            tick1 = tick + 15 # 前回の取得から15tick内に新たにぷよが設置されたと判定された場合はおそらく間違っているため除外する
            # cv2.imshow("test1", image) # 確認用
            # key = cv2.waitKey(30)
            # if key == 27:
            #     break
            
        if (check_n[1] or check_s[1]) and not skip2 and tick2 < tick:
            field = get_field(image, frames[1]) # 相手の盤面
            field_dict["fields"][1].append({"tick":tick, "rensa":check_s[1], "field":field})
            tick2 = tick + 15

        tick += 1
        image_ = image
        skip1, skip2 = check_s[0] or check_n[0], check_n[1] or check_s[1]


    dict["games"].append(field_dict)
    with open("fieldJSON\\" + ids[n - 2] + ".json", "w") as i:
        json.dump(dict, i, indent = 4, ensure_ascii=False)

    # メモリの解放
    video.release()
    cv2.destroyAllWindows()
    os.remove(ids[n - 2] + ".webm")

