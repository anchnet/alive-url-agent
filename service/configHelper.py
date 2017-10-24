import json
import time

# configure
CONFIG = None


def load_config():
    global CONFIG
    with open("cfg.json", "rb") as f:
        CONFIG = json.load(f)


def write_config():
    global CONFIG
    with open("cfg.json", "w") as f:
        json.dump(CONFIG, f, indent=4)


def sync_targets():
    while True:
        time.sleep(300)
        write_config()
