import os
import cv2
import notifier
import camutils as cutils
from camutils import CAMCONF
from datetime import datetime, timedelta


class VideoWriter:

    def __init__(self, width, height, fps, path=None):
        
        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("Invalid width or height value. Width and height must be integers")
        if width <= 0 or height <= 0:
            raise ValueError("Invalid width or height value. Width and height must be positive integers")
        if not isinstance(fps, (int, float)):
            raise ValueError("Invalid fps value. FPS must be a number")

        self.width = width
        self.height = height
        self.fps = max(fps, 1)
        self.start_time = datetime.now()
        self.max_duration = cutils.min_to_sec(CAMCONF.MAX_DURATION.value)
        self.max_size = cutils.mb_to_byte(CAMCONF.MAX_SIZE.value)
        self.current_file_index = 0
        self.writer = None
        self.frame_buffer = []

        if path:
            self.record_path = path
        else:
            self.record_path = cutils.name_file(file_index=self.current_file_index)

        try:
            self.open_new_writer()
            if not self.writer:
                raise IOError("Failed to create VideoWriter")

        except Exception as e:
            self.release()
            raise IOError(f"Failed to initialize VideoWriter: {str(e)}")

    def open_new_writer(self):
        self.current_file_index += 1
        self.codec = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            self.record_path,
            self.codec,
            self.fps,
            (self.width, self.height),
            True
        )
        self.start_time = datetime.now()

    def write(self, frame):
        self.frame_buffer.append(frame)
        if len(self.frame_buffer) >= self.fps:
            self.flush_buffer()
        if self.max_duration and (datetime.now() - self.start_time).total_seconds() >= self.max_duration:
            self.rotate_writer()

        if self.max_size and os.path.getsize(self.record_path) >= self.max_size:
            self.rotate_writer()
            
    def flush_buffer(self):
        if self.writer:
            for frame in self.frame_buffer:
                self.writer.write(frame)
            self.frame_buffer.clear()

    def rotate_writer(self):
        self.flush_buffer()
        self.release()
        self.writer_waiting = True
        self.open_new_writer()

    def release(self):
        if self.writer:
            self.flush_buffer()
            self.writer.release()
            self.writer = None

    def close(self):
        self.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class VideoProcessor:

    def __init__(self, source):
        
        self.video_source_flag = False
        try:
            try:
                self.video_source = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                self.video_source_flag = True
            except Exception as e:
                print(f"Failed to open video source using  DSHOW backend: {str(e)}")
                try:
                    self.video_source = cv2.VideoCapture(source, cv2.CAP_MSMF)
                    self.video_source_flag = True
                except Exception as e:
                    print(f"Failed to open video source using MSMF backend: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to open video source {source}: {str(e)}")
        finally:
            if self.video_source_flag is False:
                raise OSError(f"Failed to open video source {source}")
        
        self.width = int(self.video_source.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video_source.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.video_source.get(cv2.CAP_PROP_FPS))
        if self.fps == 0:
            self.fps = 30
            
        self.motion_end_time = None
        self.motion_writer = None

        self.notification_method = CAMCONF.NOTIFICATION_METHOD.value
        self.notifier = None

    def detect_motion(self, frame, gray, before):

        if frame is None or gray is None or before is None:
            return False
        try:
            before = cv2.convertScaleAbs(before)
            frame_delta = cv2.absdiff(before, gray)
            thresh = cv2.threshold(frame_delta, CAMCONF.THRESHOLD.value, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = False
            
            for target in contours:
                x, y, w, h = cv2.boundingRect(target)
                if w < 30 or cv2.contourArea(target) < 1000:
                    continue
                cv2.rectangle(frame, (x, y), (x + w, y + h), CAMCONF.BOUNDING_COLOR.value, 2)
                motion_detected = True

            return motion_detected
        
        except cv2.error as e:
            print(f"cv2Error: {str(e)}")
            return False

    def process_frames(self):

        try:
            with VideoWriter(self.width, self.height, self.fps) as default_writer:
                before = None
                while True:
                    ret, frame = self.video_source.read()
                    if not ret:
                        break
                    
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    if before is None:
                        before = gray.copy().astype("float")
                        continue

                    cv2.accumulateWeighted(gray, before, CAMCONF.WEIGHT.value)
                    if self.detect_motion(frame, gray, before):
                        if self.motion_writer is None:
                            self.motion_writer = VideoWriter(
                                self.width,
                                self.height,
                                self.fps,
                                path=cutils.name_file(motion=True)
                            )
                            self.motion_end_time = datetime.now() + timedelta(minutes=CAMCONF.MOTION_RECORD_LENGTH.value)
                        self.motion_writer.write(frame)
                        
                        # initialize Notifier and send notification
                        
                        if self.notifier is None:
                            get_notifier_class = getattr(notifier, f"{self.notification_method}Notifier")
                            self.notifier = get_notifier_class()
                            self.notifier.initialize_notifier()
                            self.notifier.process_notification(f"Motion Detected: {cutils.get_current_time()}")
                            self.notifier.notify_to_admin()
                            
                        elif self.notifier is not None and self.notifier.status == notifier.STATUS.WAITING:
                            self.notifier.process_notification(f"Motion Detected: {cutils.get_current_time()}")
                            self.notifier.notify_to_admin()
                            
                        elif self.notifier is not None and self.notifier.status == notifier.STATUS.THROTTLED:
                            pass
                         
                        elif self.motion_writer and datetime.now() > self.motion_end_time:
                            self.notifier.set_notifier_status_waiting()
                            self.motion_writer.release()
                            self.motion_writer = None
                        
                    default_writer.write(frame)
                    cv2.imshow('target_frame', frame)
                    if cv2.waitKey(1) == ord('q'):
                        break

        finally:
            self.release()

    def release(self):
        if hasattr(self, 'motion_writer') and self.motion_writer:
            self.motion_writer.release()
            self.motion_writer = None
            self.motion_end_time = None

        if hasattr(self, 'video_source') and self.video_source:
            self.video_source.release()
            self.video_source = None
            
        if hasattr(self, 'notifier') and self.notifier:
            self.notifier.close_notifier()
            self.notifier = None

        cv2.destroyAllWindows()

    def close(self):
        self.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def main():    
    source = CAMCONF.CAMERA_SOURCE.value
    print(f"trying to open camera source: {source}")
    with VideoProcessor(source) as processor:
        processor.process_frames()


if __name__ == "__main__":
    main()
