import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://kaneki:Ozzxt1qHA2hrUxNo@sidinacupc.gwqv0xz.mongodb.net/sidinacupc?retryWrites=true&w=majority&appName=sidinacupc'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'