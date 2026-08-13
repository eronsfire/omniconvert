import os

APP_VERSION = "0.9.9.6.1"
GITHUB_REPO = "eronsfire/omniconvert"
DOWNLOAD_DIR_FALLBACK = "/sdcard/Download"

def get_download_path() -> str:
    primary = "/storage/emulated/0/Download"
    return primary if os.path.exists(primary) else DOWNLOAD_DIR_FALLBACK