import cv2
import time
import numpy as np
from datetime import datetime

class captureTest:

    def __init__(self, source):
        self.videoSource = cv2.VideoCapture(source)
        self.boundingColor = (0, 0, 255) #red
        self.width = int(self.videoSource.get(3))
        self.height = int(self.videoSource.get(4))
        self.size = (self.height, self.width)
        self.path = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".mp4"
        self.fps = int(self.videoSource.get(cv2.CAP_PROP_FPS))
        self.codec = cv2.VideoWriter_fourcc(*"h264")
        self.writer = cv2.VideoWriter(self.path, self.codec, self.fps, (self.width, self.height), 1) #replace this later

    def showVideo(self):
        before = None
        while True:
            ret, frame = self.videoSource.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if before is None:
                before = gray.copy().astype("float")
                continue

            cv2.accumulateWeighted(gray, before, 0.75)
            frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(before))
            thresh = cv2.threshold(frameDelta, 3, 255, cv2.THRESH_BINARY)[1]
            contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

            for target in contours:
                x, y, w, h = cv2.boundingRect(target)
                if w < 30:
                    continue
                cv2.rectangle(frame, (x, y), (x + w, y + h), self.boundingColor, 2)

            time.sleep(1 / self.fps)
            cv2.imshow('target_frame', frame)
            self.recordVideo(frame)
            if cv2.waitKey(1) == ord('q'):
                break

        self.writer.release()
        self.videoSource.release()
        cv2.destroyAllWindows()

    def recordVideo(self, frame):
        self.writer.write(frame)

def main():
    source = "walking people.mp4"
    player = captureTest(source)
    player.showVideo()

if __name__ == "__main__":
    main()