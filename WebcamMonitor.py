import os
import cv2
import configparser
from pathlib import Path
from datetime import datetime, timedelta

# デフォルト設定
DEFAULT_CONFIG = {
    "VIDEO": {
        "SOURCE": "0",
        "MOTION_PATH": "motion-detected/",
        "MAX_DURATION": "30",  # 分単位で設定。デフォルトは30分
        "MAX_SIZE": "100"  # MB単位で設定。デフォルトは100MB
    }
}


def load_config():
    config = configparser.ConfigParser()
    config_path = "config.ini"

    # 設定ファイルが存在しない場合は作成
    if not Path(config_path).exists():
        config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
        with open(config_path, "w", encoding='utf-8') as configfile:
            config.write(configfile)
    else:
        # 設定ファイルが存在する場合は読み込み
        config.read(config_path, encoding='utf-8')
        
        # VIDEOセクションが存在しない場合はデフォルト設定を追加
        if not config.has_section("VIDEO"):
            config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
            with open(config_path, "w", encoding='utf-8') as configfile:
                config.write(configfile)

    video_config = config["VIDEO"]

    # ソースが数字でないか0未満の場合はエラー
    if not video_config["SOURCE"].isdigit() or int(video_config["SOURCE"]) < 0:
        if not (isinstance(video_config["SOURCE"], str) and video_config["SOURCE"].endswith(".mp4")):
            raise ValueError("Invalid source value in config file")

    # 動体検知時の保存パスが文字列でない場合はエラー
    if not isinstance(video_config["MOTION_PATH"], str):
        raise ValueError("Invalid motion path value in config file")
    
    # 最大録画時間が数字でないか0未満の場合はエラー
    if not video_config["MAX_DURATION"].isdigit() or int(video_config["MAX_DURATION"]) < 0:
        raise ValueError("Invalid max duration value in config file")
    
    #最大ファイルサイズが数字でないか0未満の場合はエラー
    if not video_config["MAX_SIZE"].isdigit() or int(video_config["MAX_SIZE"]) < 0:
        raise ValueError("Invalid max size value in config file")

    # 動体検知時の保存パスを作成。既に存在する場合は無視
    os.makedirs(video_config["MOTION_PATH"], exist_ok=True)
    return video_config

def min_to_sec(minutes):
    return minutes * 60

def mb_to_byte(mb):
    return mb * 1024 * 1024

class VideoWriter:

    CONFIG = load_config()
    MOTION_PATH = CONFIG["MOTION_PATH"]
    MAX_DURATION = int(CONFIG["MAX_DURATION"]) if CONFIG["MAX_DURATION"] else None
    MAX_SIZE = int(CONFIG["MAX_SIZE"]) if CONFIG["MAX_SIZE"] else None

    def __init__(self, width, height, fps, path=None):

        # 引数のチェック処理
        if width <= 0 or height <= 0:
            raise ValueError("Invalid width or height value. Width and height must be positive integers")
        if not isinstance(fps, (int, float)):
            raise ValueError("Invalid fps value. FPS must be a number")

        self.width = width
        self.height = height
        self.fps = max(fps, 1)  # fpsが0以下の場合は1に設定
        self.start_time = datetime.now()
        self.max_duration = min_to_sec(self.MAX_DURATION)
        self.max_size = mb_to_byte(self.MAX_SIZE)
        self.current_file_index = 0

        if path:
            # 動体検知時の保存パス
            self.base_path = os.path.join(self.MOTION_PATH, path)
        else:
            # デフォルトの保存パス
            self.base_path = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        try:
            self._open_new_writer()
            
            # 初期化に失敗した場合は例外を発生
            if not self.writer.isOpened():
                raise IOError("Failed to create VideoWriter")
        
        # その他の例外の場合は終了処理をし例外を発生
        except Exception as e:
            self.release()
            raise IOError(f"Failed to initialize VideoWriter: {str(e)}")

    def _open_new_writer(self):
        # base_pathを元に新しいファイル名を生成
        self.record_path = f"{self.base_path}_part{self.current_file_index}.mp4"
        self.current_file_index += 1

        # ビデオライターの初期化
        self.codec = cv2.VideoWriter_fourcc(*"h264")  # h264形式で保存
        self.writer = cv2.VideoWriter(
            self.record_path,
            self.codec,
            self.fps,
            (self.width, self.height),
            True
        )
        self.start_time = datetime.now()

    def write(self, frame):
        self.writer.write(frame)

        # 経過時間のチェック
        if self.max_duration and (datetime.now() - self.start_time).total_seconds() >= self.max_duration:
            self._rotate_writer()

        # ファイルサイズのチェック
        if self.max_size and os.path.getsize(self.record_path) >= self.max_size:
            self._rotate_writer()

    def _rotate_writer(self):
        self.release()
        self._open_new_writer()

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

    BOUNDING_COLOR = (0, 0, 255)  # 動体検知時のバウンディングボックスの色
    THRESHOLD = 10  # 二値化の閾値
    ACCUMULATED＿WEIGHT = 0.6

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
        self.accumulated_weight = self.ACCUMULATED_WEIGHT  # 移動平均の重み
        self.motion_end_time = None
        self.motion_writer = None

    def detect_motion(self, frame, gray, before):

        if frame is None or gray is None or before is None:
            return False
        try:
            before = cv2.convertScaleAbs(before)  # 絶対値を取得
            frame_delta = cv2.absdiff(before, gray)
            thresh = cv2.threshold(frame_delta, self.THRESHOLD, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion_detected = False
            for target in contours:
                x, y, w, h = cv2.boundingRect(target)
                # バウンディングボックスの幅が30未満または面積が1000未満の場合は無視
                if w < 30 or cv2.contourArea(target) < 1000:
                    continue
                cv2.rectangle(frame, (x, y), (x + w, y + h), self.boundingColor, 2)
                motion_detected = True

            return motion_detected  # 動体検知がある場合はTrueを返す
        except cv2.error as e:
            print(f"cv2Error: {str(e)}")
            return False

    def show_video(self):

        try:
            before = None  # 前フレーム。初期値はNone
            with VideoWriter(self.width, self.height, self.fps) as default_writer:
                while True:
                    ret, frame = self.videoSource.read()
                    if not ret:  # フレームが取得できない場合は終了
                        break

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    if cv2.waitKey(int(1000 / self.fps)) == ord('q'):  # qキーで終了
                        break
                    # 以下動体検知セクション。前フレームがNoneの場合はスキップ
                    if before is None:
                        before = gray.copy().astype("float")
                        continue

                    cv2.accumulateWeighted(gray, before, self.accumulated_weight)  # 移動平均を取得

                    if self.detect_motion(frame, gray, before):  # 動体検知がある場合別フォルダに保存
                        if self.motion_writer is None:
                            self.motion_writer = VideoWriter(
                                self.width,
                                self.height,
                                self.fps,
                                path="motion_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4"
                            )
                            self.motion_end_time = datetime.now() + timedelta(minutes=10)  # 動体検知時の保存時間を10分に設定
                        self.motion_writer.write(frame)
                    elif self.motion_writer and datetime.now() > self.motion_end_time:  # 動体検知時の保存時間が経過した場合は保存を終了
                        self.motion_writer.release()
                        self.motion_writer = None

                    cv2.imshow('target_frame', frame)  # 処理後フレームを表示
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
    source = int(config["SOURCE"]) if config["SOURCE"].isdigit() else config["SOURCE"]
    with CaptureVideo(source) as player:
        player.show_video()


if __name__ == "__main__":
    main()