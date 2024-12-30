import os
import configparser
from enum import Enum
from pathlib import Path
from datetime import datetime

# Default Configuration

DEFAULT_CONFIG = {
    "VIDEO": {
        "SOURCE": "0",
        "MOTION_PATH": "motion-detected/",
        "MAX_DURATION": "30",  # minutes
        "MAX_SIZE": "100",  # MB
        "MOTION_RECORD_LENGTH": "10"  # minutes
    },
    "NOTIFICATION METHOD": {
        "METHOD": "Line"
    },
    "LINE": {
        "TOKEN": "PUT YOUR TOKEN HERE"
    },
    "EMAIL": {
        "NOTIFIER_GMAIL": "PUT YOUR NOTIFIER GMAIL HERE",
        "NOTIFIER_PASSWORD": "PUT YOUR NOTIFIER PASSWORD HERE",
        "ADMIN_EMAIL": "PUT YOUR ADMIN EMAIL HERE",
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587"
    }
}

_global_config = None


def load_config():
    global _global_config
    
    if _global_config is not None:
        return _global_config
    
    config = configparser.ConfigParser()
    config_path = "config.ini"

    if not Path(config_path).exists():
        config.read_dict(DEFAULT_CONFIG)
        with open(config_path, "w", encoding='utf-8') as configfile:
            config.write(configfile)
    else:
        config.read(config_path, encoding='utf-8')
        
        if not config.has_section("VIDEO"):
            config["VIDEO"] = DEFAULT_CONFIG["VIDEO"]
            with open(config_path, "w", encoding='utf-8') as configfile:
                config.write(configfile)
                
        if not config.has_section("LINE"):
            config["LINE"] = DEFAULT_CONFIG["LINE"]
            with open(config_path, "w", encoding='utf-8') as configfile:
                config.write(configfile)
                
        if not config.has_section("EMAIL"):
            config["EMAIL"] = DEFAULT_CONFIG["EMAIL"]
            with open(config_path, "w", encoding='utf-8') as configfile:
                config.write(configfile)

    # Validation Section

    if not config["VIDEO"]["SOURCE"].isdigit() or int(config["VIDEO"]["SOURCE"]) < 0:
        if not (isinstance(config["VIDEO"]["SOURCE"], str) and config["VIDEO"]["SOURCE"].endswith(".mp4")):
            raise ValueError("Invalid source value in config file")

    if not isinstance(config["VIDEO"]["MOTION_PATH"], str):
        raise ValueError("Invalid motion path value in config file")

    if not config["VIDEO"]["MAX_DURATION"].isdigit() or int(config["VIDEO"]["MAX_DURATION"]) < 0:
        raise ValueError("Invalid max duration value in config file")
    
    if not config["VIDEO"]["MAX_SIZE"].isdigit() or int(config["VIDEO"]["MAX_SIZE"]) < 0:
        raise ValueError("Invalid max size value in config file")
    
    if not config["VIDEO"]["MOTION_RECORD_LENGTH"].isdigit() or int(config["VIDEO"]["MOTION_RECORD_LENGTH"]) < 0:
        raise ValueError("Invalid motion record length value in config file")
    
    try:
        os.makedirs(config["VIDEO"]["MOTION_PATH"], exist_ok=True)
        
    except Exception as e:
        raise OSError(f"Failed to create motion path directory: {str(e)}")
    
    _global_config = config
    return _global_config


def min_to_sec(minutes):
    return minutes * 60


def mb_to_byte(mb):
    return mb * 1024 * 1024


class CAMCONF(Enum):
    CONFIG = load_config()
    
    # Video Configuration
    
    CAMERA_SOURCE = int(CONFIG["VIDEO"]["SOURCE"]) if CONFIG["VIDEO"]["SOURCE"].isdigit() else CONFIG["VIDEO"]["SOURCE"]
    MOTION_PATH = CONFIG["VIDEO"]["MOTION_PATH"]
    MAX_DURATION = int(CONFIG["VIDEO"]["MAX_DURATION"]) if CONFIG["VIDEO"]["MAX_DURATION"] else None
    MAX_SIZE = int(CONFIG["VIDEO"]["MAX_SIZE"]) if CONFIG["VIDEO"]["MAX_SIZE"] else None
    MOTION_RECORD_LENGTH = int(CONFIG["VIDEO"]["MOTION_RECORD_LENGTH"])
    BOUNDING_COLOR = (0, 0, 255)
    THRESHOLD = 10
    WEIGHT = 0.6
    
    # Notifier Configuration
    
    NOTIFICATION_METHOD = CONFIG["NOTIFICATION METHOD"]["METHOD"]
    LINE_TOKEN = CONFIG["LINE"]["TOKEN"] if CONFIG["LINE"]["TOKEN"] else None
    NOTIFIER_EMAIL = CONFIG["EMAIL"]["NOTIFIER_GMAIL"] if CONFIG["EMAIL"]["NOTIFIER_GMAIL"] else None
    NOTIFIER_PASSWORD = CONFIG["EMAIL"]["NOTIFIER_PASSWORD"] if CONFIG["EMAIL"]["NOTIFIER_PASSWORD"] else None
    ADMIN_EMAIL = CONFIG["EMAIL"]["ADMIN_EMAIL"] if CONFIG["EMAIL"]["ADMIN_EMAIL"] else None
    SMTP_SERVER = CONFIG["EMAIL"]["SMTP_SERVER"] if CONFIG["EMAIL"]["SMTP_SERVER"] else None
    SMTP_PORT = int(CONFIG["EMAIL"]["SMTP_PORT"]) if CONFIG["EMAIL"]["SMTP_PORT"] else None


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def name_file(file_index=None, motion=None, extension=".mp4"):
    '''
    file_index: int
    motion: bool
    '''
    current_time = get_current_time()
    if motion:
        return f"{CAMCONF.MOTION_PATH.value}motion_{current_time}{extension}"
    
    if file_index is not None:
        if isinstance(file_index, int) is False:
            return f"{current_time}_{int(file_index)}{extension}"
        else:
            return f"{current_time}_{file_index}{extension}"
    
    if file_index is None and motion is None:
        raise ValueError("file_index or motion must be specified")


if __name__ == "__main__":
    load_config()
