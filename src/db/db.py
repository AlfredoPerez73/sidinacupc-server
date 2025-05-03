from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import json
from datetime import datetime

mongo = PyMongo()

def initialize_db(app):
    mongo.init_app(app)
    return mongo

# Clase auxiliar para trabajar con ObjectId de MongoDB
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

# Función para serializar documentos MongoDB
def serialize_doc(doc):
    if doc is None:
        return None
    doc['_id'] = str(doc['_id'])
    return doc

# Función para serializar una lista de documentos MongoDB
def serialize_list(docs):
    return [serialize_doc(doc) for doc in docs]