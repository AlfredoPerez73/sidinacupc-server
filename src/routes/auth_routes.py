from flask import Blueprint, request, jsonify, current_app
from db.db import mongo
from middlewares.auth import generate_token
import bcrypt
import jwt
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra un nuevo usuario"""
    data = request.json
    
    # Validar datos requeridos
    required_fields = ['email', 'password', 'nombre', 'rol']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'El campo {field} es requerido'}), 400
    
    # Verificar si ya existe un usuario con el mismo email
    existing_user = mongo.db.usuarios.find_one({'email': data['email']})
    
    if existing_user:
        return jsonify({'message': 'El email ya está registrado'}), 400
    
    # Hashear la contraseña
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Crear el usuario
    new_user = {
        'email': data['email'],
        'password': hashed_password,
        'nombre': data['nombre'],
        'rol': data['rol'],
        'estado': 'activo'
    }
    
    result = mongo.db.usuarios.insert_one(new_user)
    
    # Generar token
    token = generate_token(result.inserted_id)
    
    return jsonify({
        'message': 'Usuario registrado exitosamente',
        'id_user': str(result.inserted_id),
        'token': token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicia sesión de un usuario"""
    data = request.json
    
    # Validar datos requeridos
    if 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Email y password son requeridos'}), 400
    
    # Buscar usuario por email
    user = mongo.db.usuarios.find_one({'email': data['email']})
    
    if not user:
        return jsonify({'message': 'Credenciales inválidas'}), 401
    
    # Verificar contraseña
    if bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        # Generar token
        token = generate_token(user['_id'])
        
        response = jsonify({
            'message': 'Inicio de sesión exitoso',
            'id_user': str(user['_id']),
            'nombre': user['nombre'],
            'rol': user['rol'],
            'token': token
        })
    
        # Establecer la cookie con el token
        response.set_cookie(
            'auth_token',
            token,
            httponly=True,
            secure=False,  # Cambiar a True en producción con HTTPS
            max_age=60*60*24  # 1 día
        )
        
        return response

@auth_bp.route('/user', methods=['GET'])
def get_user():
    """Obtiene información del usuario actual"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(
            token, 
            current_app.config.get('JWT_SECRET_KEY'),
            algorithms=['HS256']
        )
        
        id_user = payload['sub']
        user = mongo.db.usuarios.find_one({'_id': ObjectId(id_user)})
        
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'id_user': str(user['_id']),
            'email': user['email'],
            'nombre': user['nombre'],
            'rol': user['rol']
        })
        
    except Exception as e:
        return jsonify({'message': f'Token inválido: {str(e)}'}), 401
    
@auth_bp.route('/verifyToken', methods=['GET'])
def verify_token():
    """Verifica la validez del token y devuelve la información del usuario"""
    # Intentar obtener el token de las cookies primero
    token = request.cookies.get('auth_token')
    
    # Si no está en cookies, buscar en el header de Authorization
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and ' ' in auth_header:
            token = auth_header.split(" ")[1]
    
    # Si no hay token en ninguna parte, devolver error
    if not token:
        return jsonify({
            'message': 'No se proporcionó token de autenticación'
        }), 401
    
    try:
        # Verificar el token
        payload = jwt.decode(
            token, 
            current_app.config.get('JWT_SECRET_KEY'),
            algorithms=['HS256']
        )
        
        # Obtener el ID del usuario del payload
        id_user = payload['sub']
        
        # Buscar el usuario en la base de datos
        user = mongo.db.usuarios.find_one({'_id': ObjectId(id_user)})
        
        # Si el usuario no existe
        if not user:
            return jsonify({
                'message': 'Usuario no encontrado o token inválido'
            }), 401
        
        # Si todo está bien, devolver los datos del usuario
        return jsonify({
            'id_user': str(user['_id']),
            'email': user['email'],
            'nombre': user['nombre'],
            'rol': user['rol'],
            'authenticated': True
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({
            'message': 'Token expirado'
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            'message': 'Token inválido'
        }), 401
    except Exception as e:
        return jsonify({
            'message': f'Error al verificar token: {str(e)}'
        }), 401