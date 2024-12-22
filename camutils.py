import os
import configparser
from enum import Enum
from pathlib import Path
from datetime import datetime

# デフォルト設定
DEFAULT_CONFIG = {
    "VIDEO": {
        "SOURCE": "0",
        "MOTION_PATH": "motion-detected/",
        "MAX_DURATION": "30",  # minutes
        "MAX_SIZE": "100",  # MB
        "MOTION_RECORD_LENGTH": "10"  # minutes
    }
}


def load_config():
    config = configparser.ConfigParser()
    config_path = "config.ini"

    if not Path(config_path).exists():
        config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
        with open(config_path, "w", encoding='utf-8') as configfile:
            config.write(configfile)
    else:
        config.read(config_path, encoding='utf-8')
        
        if not config.has_section("VIDEO"):
            config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
            with open(config_path, "w", encoding='utf-8') as configfile:
                config.write(configfile)

    video_config = config["VIDEO"]

    if not video_config["SOURCE"].isdigit() or int(video_config["SOURCE"]) < 0:
        if not (isinstance(video_config["SOURCE"], str) and video_config["SOURCE"].endswith(".mp4")):
            raise ValueError("Invalid source value in config file")

    if not isinstance(video_config["MOTION_PATH"], str):
        raise ValueError("Invalid motion path value in config file")

    if not video_config["MAX_DURATION"].isdigit() or int(video_config["MAX_DURATION"]) < 0:
        raise ValueError("Invalid max duration value in config file")
    
    if not video_config["MAX_SIZE"].isdigit() or int(video_config["MAX_SIZE"]) < 0:
        raise ValueError("Invalid max size value in config file")
    
    if not video_config["MOTION_RECORD_LENGTH"].isdigit() or int(video_config["MOTION_RECORD_LENGTH"]) < 0:
        raise ValueError("Invalid motion record length value in config file")
    
    try:
        os.makedirs(video_config["MOTION_PATH"], exist_ok=True)
        
    except Exception as e:
        raise OSError(f"Failed to create motion path directory: {str(e)}")
    
    return video_config

def min_to_sec(minutes):
    return minutes * 60

def mb_to_byte(mb):
    return mb * 1024 * 1024


class CAMCONF(Enum):
    CONFIG = load_config()
    CAMERA_SOURCE = int(CONFIG["SOURCE"]) if CONFIG["SOURCE"].isdigit() else CONFIG["SOURCE"]
    MOTION_PATH = CONFIG["MOTION_PATH"]
    MAX_DURATION = int(CONFIG["MAX_DURATION"]) if CONFIG["MAX_DURATION"] else None
    MAX_SIZE = int(CONFIG["MAX_SIZE"]) if CONFIG["MAX_SIZE"] else None
    MOTION_RECORD_LENGTH = int(CONFIG["MOTION_RECORD_LENGTH"])
    BOUNDING_COLOR = (0, 0, 255)
    THRESHOLD = 10
    WEIGHT = 0.6


def name_file(file_index=None, motion=None, extension=".mp4"):
    '''
    file_index: int
    motion: bool
    '''
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if motion:
        return f"{CAMCONF.MOTION_PATH.value}motion_{current_time}{extension}"
    
    if file_index is not None and isinstance(file_index, int):
        return f"{current_time}_{file_index}{extension}"
    
    if file_index is None and motion is None:
        raise ValueError("file_index or motion must be specified")
