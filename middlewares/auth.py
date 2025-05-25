import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from bson.objectid import ObjectId
from db.db import mongo

def generate_token(user_id):
    """Genera un token JWT para un usuario"""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': str(user_id)
    }
    return jwt.encode(
        payload,
        current_app.config.get('JWT_SECRET_KEY'),
        algorithm='HS256'
    )

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Primero, intenta extraerlo desde el header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': 'Token mal formado'}), 401
        
        # Si no está en el header, intenta desde la cookie (opcional)
        if not token:
            token = request.cookies.get('auth_token')
        
        if not token:
            return jsonify({'message': 'Token no proporcionado'}), 401
        
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('JWT_SECRET_KEY'),
                algorithms=['HS256']
            )
            user_id = payload['sub']
            current_user = mongo.db.usuarios.find_one({'_id': ObjectId(user_id)})
            
            if not current_user:
                return jsonify({'message': 'Usuario no encontrado'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorador para verificar si el usuario es administrador"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.get('role') == 'admin':
            return jsonify({'message': 'Se requieren permisos de administrador'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated