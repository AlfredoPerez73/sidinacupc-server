from flask import Blueprint, request, jsonify
from models.estudiante import Estudiante
from services.estudiante_services import EstudianteService
from db.db import serialize_doc, serialize_list
from middlewares.auth import token_required


estudiantes_bp = Blueprint('estudiantes', __name__)

@estudiantes_bp.route('/', methods=['GET'])
@token_required
def get_estudiantes(current_user):
    """Obtiene la lista de estudiantes"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Procesar filtros
    filters = {}
    if 'nombre' in request.args:
        filters['nombre_completo'] = {'$regex': request.args.get('nombre'), '$options': 'i'}
    if 'programa' in request.args:
        filters['programa_academico'] = request.args.get('programa')
    if 'facultad' in request.args:
        filters['facultad'] = request.args.get('facultad')
    if 'estado' in request.args:
        filters['estado'] = request.args.get('estado')
    
    result = Estudiante.get_all(filters, page, per_page)
    
    return jsonify({
        'estudiantes': serialize_list(result['estudiantes']),
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages']
    })
    
@estudiantes_bp.route('/importar', methods=['POST'])
@token_required
def importar_estudiantes(current_user):
    # Verificar permisos (solo administradores)
    if current_user['rol'] != 'admin':
        return jsonify({'message': 'No tiene permisos para realizar esta acción'}), 403
    
    # Verificar archivo
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = EstudianteService.importar_csv(file)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'estudiantes_creados': result['estudiantes_creados'],
        'errores': result['errores']
    })

@estudiantes_bp.route('/<id_estudiante>', methods=['GET'])
@token_required
def get_estudiante(current_user, id_estudiante):
    """Obtiene un estudiante por su ID"""
    estudiante = Estudiante.get_by_id(id_estudiante)
    
    if not estudiante:
        return jsonify({'message': 'Estudiante no encontrado'}), 404
    
    return jsonify(serialize_doc(estudiante))

@estudiantes_bp.route('/', methods=['POST'])
@token_required
def create_estudiante(current_user):
    """Crea un nuevo estudiante"""
    data = request.json
    
    # Validar datos requeridos
    required_fields = ['nombre_completo', 'programa_academico', 'facultad', 
                        'documento_identidad', 'tipo_documento', 'email']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'El campo {field} es requerido'}), 400
    
    # Verificar si ya existe un estudiante con el mismo documento
    existing = Estudiante.get_by_documento(data['documento_identidad'])
    if existing:
        return jsonify({'message': 'Ya existe un estudiante con este documento de identidad'}), 400
    
    # Crear el estudiante
    id_estudiante = Estudiante.create(data)
    
    return jsonify({
        'message': 'Estudiante creado exitosamente',
        'id_estudiante': id_estudiante
    }), 201

@estudiantes_bp.route('/<id_estudiante>', methods=['PUT'])
@token_required
def update_estudiante(current_user, id_estudiante):
    """Actualiza un estudiante existente"""
    data = request.json
    
    estudiante = Estudiante.get_by_id(id_estudiante)
    if not estudiante:
        return jsonify({'message': 'Estudiante no encontrado'}), 404
    
    updated = Estudiante.update(id_estudiante, data)
    
    return jsonify({
        'message': 'Estudiante actualizado exitosamente',
        'estudiante': serialize_doc(updated)
    })

@estudiantes_bp.route('/<id_estudiante>', methods=['DELETE'])
@token_required
def delete_estudiante(current_user, id_estudiante):
    """Elimina un estudiante (cambio de estado a inactivo)"""
    estudiante = Estudiante.get_by_id(id_estudiante)
    if not estudiante:
        return jsonify({'message': 'Estudiante no encontrado'}), 404
    
    Estudiante.delete(id_estudiante)
    
    return jsonify({
        'message': 'Estudiante eliminado exitosamente'
    })

@estudiantes_bp.route('/<id_estudiante>/requisitos-intercambio', methods=['GET'])
@token_required
def verificar_requisitos(current_user, id_estudiante):
    """Verifica si un estudiante cumple con los requisitos para intercambio"""
    estudiante = Estudiante.get_by_id(id_estudiante)
    if not estudiante:
        return jsonify({'message': 'Estudiante no encontrado'}), 404
    
    cumple, mensaje = Estudiante.cumple_requisitos_intercambio(id_estudiante)
    
    return jsonify({
        'cumple_requisitos': cumple,
        'mensaje': mensaje
    })