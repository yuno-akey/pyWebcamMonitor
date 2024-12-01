import os
import cv2
import configparser
from pathlib import Path
from datetime import datetime, timedelta

def load_config():
    config = configparser.ConfigParser()
    config_path = "config.ini"
    if not Path(config_path).exists(): # 設定ファイルが存在しない場合は作成
        config["VIDEO"] = {
            "SOURCE": 0, # カメラソース (デフォルトは0=内蔵カメラ)
            "MOTION_PATH": "motion-detected/" # 動体検知時の保存パス
        }
        with open(config_path, "w", encoding = 'utf-8') as configfile:
            config.write(configfile)
        os.makedirs(config["VIDEO"]["MOTION_PATH"], exist_ok=True) # 動体検知時の保存パスを作成
    else:
        config.read(config_path, encoding='utf-8')
    return config["VIDEO"]



class VideoWriter:
    CONFIG = load_config()
    MOTION_PATH = CONFIG["MOTION_PATH"]

    def __init__(self, width, height, fps, path=None):
        self.width = width
        self.height = height
        self.fps = fps

        if path:
            self.path = os.path.join(self.MOTION_PATH, path) # 動体検知時の保存パス
        else:
            self.path = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4" # デフォルトの保存パス

        self.codec = cv2.VideoWriter_fourcc(*"h264") #h264形式で保存. mp4vも可.
        self.writer = cv2.VideoWriter(
            self.path, 
            self.codec, 
            self.fps, 
            (self.width, self.height), 
            1 # 1:カラー, 0:グレースケール
        )
    
    def write(self, frame):
        self.writer.write(frame)
    
    def release(self):
        self.writer.release()



class CaptureVideo:

    BOUNDING_COLOR = (0, 0, 255) # 動体検知時のバウンディングボックスの色

    def __init__(self, source):
        self.videoSource = cv2.VideoCapture(source)
        self.boundingColor = self.BOUNDING_COLOR
        self.width = int(self.videoSource.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.videoSource.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.videoSource.get(cv2.CAP_PROP_FPS))
        self.ACCUMULATED_WEIGHT = 0.6 #移動平均の重み (0.6が最適)
        self.default_writer = VideoWriter(self.width, self.height, self.fps)
        self.motion_writer = None
        self.motion_end_time = None

    def detect_motion(self, frame, gray, before):
        before = cv2.convertScaleAbs(before) # 絶対値を取得
        frame_delta = cv2.absdiff(before, gray)
        thresh = cv2.threshold(frame_delta, 7, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for target in contours:
            x, y, w, h = cv2.boundingRect(target)
            if w < 30 or cv2.contourArea(target) < 1000: # バウンディングボックスの幅が30未満または面積が1000未満の場合は無視
                continue
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.boundingColor, 2)
            motion_detected = True

        return motion_detected # 動体検知がある場合はTrueを返す

    def showVideo(self):
        before = None # 前フレーム
        while True:
            ret, frame = self.videoSource.read()
            if not ret: # フレームが取得できない場合は終了
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if before is None:
                before = gray.copy().astype("float")
                continue

            cv2.accumulateWeighted(gray, before, self.ACCUMULATED_WEIGHT) # 移動平均を取得
            
            if self.detect_motion(frame, gray, before): # 動体検知がある場合別フォルダに保存
                if self.motion_writer is None:
                    self.motion_writer = VideoWriter(
                        self.width,
                        self.height,
                        self.fps,
                        path="motion_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4"
                        )
                    self.motion_end_time = datetime.now() + timedelta(minutes=10) # 動体検知時の保存時間を10分に設定
                self.motion_writer.write(frame)
            elif self.motion_writer and datetime.now() > self.motion_end_time: # 動体検知時の保存時間が経過した場合は保存を終了
                self.motion_writer.release()
                self.motion_writer = None

            cv2.imshow('target_frame', frame)
            self.default_writer.write(frame)
            if cv2.waitKey(int(1000 / self.fps)) == ord('q'): # qキーで終了
                break

        self.default_writer.release()
        self.videoSource.release()
        cv2.destroyAllWindows()

def main():
    config = load_config()
    source = config["SOURCE"]
    player = CaptureVideo(source)
    player.showVideo()

if __name__ == "__main__":
    main()