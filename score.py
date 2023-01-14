import cv2

# 検索対象画像とテンプレート画像の読み込み
template = cv2.imread('pngs\\closs_template.png')

def temp(filename):
    image = cv2.imread(filename)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh_binary = cv2.threshold(gray_image, 80, 255, cv2.THRESH_BINARY)

    # 輪郭の抽出・近似
    contours, _ = cv2.findContours(thresh_binary, 1, 2)
    contours = [cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True) for cnt in contours]

    # よしなに枠は2番目, 3番目に大きい輪郭とする
    # frames[0]が自分の枠, frames[1]が相手の枠となる
    frames = sorted(contours, key=lambda cnt: cv2.contourArea(cnt))[-3:][:2]
    frames.sort(key=lambda cnt: cv2.boundingRect(cnt)[0])

    frame = frames[0]
    x, y, w, h = cv2.boundingRect(frame)
    s, t, u, v = cv2.boundingRect(frames[1])
    # 画像の検索（Template Matching）
    result_p1 = cv2.matchTemplate(image[y+int(h/96*96):y+int(h/96*104), x+int(w/48*28):x+int(w/96*69)], template, cv2.TM_CCORR_NORMED)
    # 相手の盤面
    result_p2 = cv2.matchTemplate(image[t+v:t+int(v/96*103), s+int(u/48*19):s+int(u/12*6)], template, cv2.TM_CCORR_NORMED)
    
    # 検索結果の信頼度と位置座標の取得
    #1p側
    min_val, max_val_p1, min_loc, max_loc = cv2.minMaxLoc(result_p1)
    max_val_p1 = max_val_p1 ** 2
    #2p側
    min_val, max_val_p2, min_loc, max_loc = cv2.minMaxLoc(result_p2)
    max_val_p2 = max_val_p2 ** 2
    print(max_val_p1)
    print(max_val_p2)


temp("pngs\\sample11.png")


