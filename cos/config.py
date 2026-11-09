import os
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("COS_MODEL", "qwen3.5:4b")
DB_PATH = os.getenv("COS_DB", "cos.db")
WORKSPACE = os.path.abspath(os.getenv("COS_WORKSPACE", "./workspace"))
OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))
os.makedirs(WORKSPACE, exist_ok=True)
GUEST_PASSWORD = os.getenv("GUEST_PASSWORD", "")  # empty = guests are ignored
CODE_MODEL = os.getenv("COS_CODE_MODEL", MODEL)
