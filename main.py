import cv2
import numpy
from enum import Enum
import csv

with open('data.csv', 'w') as f:
    f.write('')

video = cv2.VideoCapture('test_video.avi')
tick = 0

while video.isOpened():
    ret, image = video.read()
    if not ret:
        break
    if tick % 60:
        tick += 1
        continue

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    _, thresh_binary = cv2.threshold(gray_image, 80, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh_binary, 1, 2)
    contours = [cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True) for cnt in contours]
    frames = sorted(contours, key=lambda cnt: cv2.contourArea(cnt))[-3:][:2]
    frames.sort(key=lambda cnt: cv2.boundingRect(cnt)[0])

    class Color(Enum):
        RED = 0
        YELLOW = 1
        GREEN = 2
        BLUE = 3
        PURPLE = 4
        OJAMA = 5

    # セル(A, B)の中点近点からHSVの平均値を取り、色を判定して返す
    def get_color_from(A, B):
        (ax, ay), (bx, by) = A, B
        dx, dy = (bx - ax) // 3, (by - ay) // 3
        hsv = numpy.array([hsv_image[j, i] for i in range(ax + dx, bx - dx) for j in range(ay + dy, by - dy)]).mean(0)
        return tuple(int(i) for i in hsv)

    fields = []  # 自分と相手の盤面

    for frame in frames:
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
            fields.append(row)

    field1 = fields[:12]  # 自分の盤面
    field2 = fields[12:]  # 相手の盤面
    fields = []
    for frame in frames:
        x, y, w, h = cv2.boundingRect(frame)
        w //= 6
        h //= 12
        points = [[(x + (i * w), y + (j * h)) for i in range(0, 7)] for j in range(0, 13)]
        for i in range(0, 12):
            row = []
            for j in range(0, 6):
                # points[i][j] が セルの左上頂点
                # points[i + 1][j + 1] が セルの右下頂点
                row.append(get_color_from(points[i][j], points[i + 1][j + 1]))
            fields.append(row)

    def print_field():
        print('\n'.join([str(f) for f in field1]))


    with open('data.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([tick, field1])

    tick += 1


# メモリの解放
video.release()
cv2.destroyAllWindows()
