import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_URI.replace('sqlite:///', ''))
    return conn