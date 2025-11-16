import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///C:/go-rest-api/storage/storage.db')