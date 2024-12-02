import os
import cv2
import configparser
from pathlib import Path
from datetime import datetime, timedelta

# デフォルト設定
DEFAULT_CONFIG = {
    "VIDEO": {
        "SOURCE": "0",
        "MOTION_PATH": "motion-detected/"
    }
}

def load_config():
    config = configparser.ConfigParser()
    config_path = "config.ini"
    motion_path = DEFAULT_CONFIG["VIDEO"]["MOTION_PATH"]

    if not Path(config_path).exists(): # 設定ファイルが存在しない場合は作成
        config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
        with open(config_path, "w", encoding = 'utf-8') as configfile:
            config.write(configfile)
    else:
        # 設定ファイルが存在する場合は読み込み
        config.read(config_path, encoding='utf-8')
        if not config.has_section("VIDEO"): #VIDEOセクションが存在しない場合はデフォルト設定を追加
            config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
            with open(config_path, "w", encoding = 'utf-8') as configfile:
                config.write(configfile)

    if not config["VIDEO"]["SOURCE"].isdigit() or int(config["VIDEO"]["SOURCE"]) < 0: # ソースが数字でないか0未満の場合はエラー
        if isinstance(config["VIDEO"]["SOURCE"], str):
            pass
        else:
            raise ValueError("Invalid source value in config file")

    if not isinstance(config["VIDEO"]["MOTION_PATH"], str): # 動体検知時の保存パスが文字列でない場合はエラー
        raise ValueError("Invalid motion path value in config file")
    else:
        motion_path = config["VIDEO"]["MOTION_PATH"]

    os.makedirs(motion_path, exist_ok=True) # 動体検知時の保存パスを作成。既に存在する場合は無視
    return config["VIDEO"]



class VideoWriter:
    CONFIG = load_config()
    MOTION_PATH = CONFIG["MOTION_PATH"]

    def __init__(self, width, height, fps, path=None):
        if width <= 0 or height <= 0:
            raise ValueError("Invalid width or height value. Width and height must be positive integers")
        if not isinstance(fps, (int, float)):
            raise ValueError("Invalid fps value. FPS must be a number")

        self.width = width
        self.height = height
        self.fps = max(fps, 1) # fpsが0以下の場合は1に設定

        if path:
            self.path = os.path.join(self.MOTION_PATH, path) # 動体検知時の保存パス
        else:
            self.path = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4" # デフォルトの保存パス

        try:
            self.codec = cv2.VideoWriter_fourcc(*"h264") #h264形式で保存. mp4vも可.
            self.writer = cv2.VideoWriter(
                self.path, 
                self.codec, 
                self.fps, 
                (self.width, self.height), 
                1 # 1:カラー, 0:グレースケール
            )
            if not self.writer.isOpened(): # 初期化に失敗した場合は例外を発生
                raise IOError("Failed to create VideoWriter")
        except Exception as e:
            self.release()
            raise IOError(f"Failed to initialize VideoWriter: {str(e)}")
    
    def write(self, frame):
        self.writer.write(frame)
    
    def release(self):
        if self.writer:
            self.writer.release()
            self.writer = None

    def close(self):
        self.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __del__(self):
        self.release()



class CaptureVideo:

    BOUNDING_COLOR = (0, 0, 255) # 動体検知時のバウンディングボックスの色

    def __init__(self, source):
        self.videoSource = cv2.VideoCapture(source)
        if not self.videoSource.isOpened():
            raise ValueError(f"Failed to open video source: {source}")
        
        self.boundingColor = self.BOUNDING_COLOR
        self.width = int(self.videoSource.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.videoSource.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.videoSource.get(cv2.CAP_PROP_FPS))
        if self.fps == 0:
            self.fps = 30
        self.ACCUMULATED_WEIGHT = 0.6 #移動平均の重み
        self.motion_end_time = None
        try:
            self.motion_writer = None
        except Exception as e:
            self.release()
            raise IOError(f"Failed to initialize CaptureVideo: {str(e)}")

    def detect_motion(self, frame, gray, before):
        if frame is None or gray is None or before is None:
            return False
        try:
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
        except cv2.error as e:
            print(f"cv2Error: {str(e)}")
            return False

    def showVideo(self):
        try:
            before = None # 前フレーム。初期値はNone
            with VideoWriter(self.width, self.height, self.fps) as default_writer:
                while True:
                    ret, frame = self.videoSource.read()
                    if not ret: # フレームが取得できない場合は終了
                        break

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    if cv2.waitKey(int(1000 / self.fps)) == ord('q'): # qキーで終了
                        break
                    # 以下動体検知セクション。前フレームがNoneの場合はスキップ
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

                    cv2.imshow('target_frame', frame) # 処理後フレームを表示
                    default_writer.write(frame)

        finally:
            if self.motion_writer:
                self.motion_writer.release()
            if self.videoSource:
                self.videoSource.release()
            cv2.destroyAllWindows()

    def release(self):
        if hasattr(self, 'motion_writer') and self.motion_writer:
            self.motion_writer.release()
            self.motion_writer = None
            self.motion_end_time = None

        if hasattr(self, 'videoSource') and self.videoSource:
            self.videoSource.release()
            self.videoSource = None

    def close(self):
        self.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __del__(self):
        self.release()

def main():
    config = load_config()
    source = config["SOURCE"]
    with CaptureVideo(source) as player:
        player.showVideo()

if __name__ == "__main__":
    main()