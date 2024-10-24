import os

API_HOSTNAME = os.getenv("API_HOSTNAME", default="")
REDIS_URL = os.getenv("REDIS_URL", default="redis://localhost:6379")
CLONE_DIR_PATH = os.getenv("CLONE_DIR_PATH", default="./.repos/")
