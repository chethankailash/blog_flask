# config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "YOUR_SECRET_KEY"
    MONGO_URI = os.environ.get("MONGO_URI") or "mongodb://localhost:27017/myblogdb"
