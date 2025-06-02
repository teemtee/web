import os

API_HOSTNAME = os.getenv("API_HOSTNAME", default="")
VALKEY_URL = os.getenv("VALKEY_URL", default="valkey://localhost:6379")
CLONE_DIR_PATH = os.getenv("CLONE_DIR_PATH", default="./.repos/")
