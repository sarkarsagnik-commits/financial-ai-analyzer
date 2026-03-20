
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env from current directory

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")