import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://AlfredoPerez73:Zc5WPwe5ntqfys8x@cluster0.5kxa2yc.mongodb.net/sidinacupc'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'