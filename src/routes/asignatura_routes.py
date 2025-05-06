from flask import Blueprint, request, jsonify
from services.asignatura_services import AsignaturaService
from middlewares.auth import token_required

asignaturas_bp = Blueprint('asignaturas', __name__)

@asignaturas_bp.route('/<asignatura_id>', methods=['GET'])
@token_required
def get_asignatura(current_user, asignatura_id):
    """Obtiene una asignatura por su ID"""
    asignatura = AsignaturaService.get_by_id(asignatura_id)
    
    if not asignatura:
        return jsonify({'message': 'Asignatura no encontrada'}), 404
    
    return jsonify(asignatura)

@asignaturas_bp.route('/importar', methods=['POST'])
@token_required
def importar_asignaturas(current_user):
    """Importa asignaturas desde un archivo CSV"""
    # Verificar permisos
    if current_user['rol'] not in ['admin', 'orpi', 'jefe_programa']:
        return jsonify({'message': 'No tiene permisos para realizar esta acción'}), 403
    
    # Verificar archivo
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    # Verificar solicitud_id en formulario
    if 'solicitud_id' not in request.form:
        return jsonify({'message': 'Se requiere el ID de la solicitud'}), 400
    
    solicitud_id = request.form['solicitud_id']
    file = request.files['file']
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = AsignaturaService.importar_csv(file, solicitud_id)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'asignaturas_creadas': result['asignaturas_creadas'],
        'errores': result['errores']
    })

@asignaturas_bp.route('/solicitud/<solicitud_id>', methods=['GET'])
@token_required
def get_asignaturas_solicitud(current_user, solicitud_id):
    """Obtiene todas las asignaturas para una solicitud específica"""
    asignaturas, mensaje = AsignaturaService.get_by_solicitud(solicitud_id)
    
    if not asignaturas:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'asignaturas': asignaturas,
        'message': mensaje
    })

@asignaturas_bp.route('/', methods=['POST'])
@token_required
def create_asignatura(current_user):
    """Crea una nueva equivalencia de asignatura"""
    data = request.json
    
    # Validar datos requeridos
    if 'solicitud_id' not in data:
        return jsonify({'message': 'El campo solicitud_id es requerido'}), 400
    
    asignatura_id, mensaje = AsignaturaService.create(data)
    
    if not asignatura_id:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'asignatura_id': asignatura_id
    }), 201

@asignaturas_bp.route('/<asignatura_id>', methods=['PUT'])
@token_required
def update_asignatura(current_user, asignatura_id):
    """Actualiza los datos de una asignatura"""
    data = request.json
    
    updated, mensaje = AsignaturaService.update(asignatura_id, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'asignatura': updated
    })

@asignaturas_bp.route('/<asignatura_id>', methods=['DELETE'])
@token_required
def delete_asignatura(current_user, asignatura_id):
    """Elimina una asignatura"""
    success, mensaje = AsignaturaService.delete(asignatura_id)
    
    if not success:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje
    })

@asignaturas_bp.route('/<asignatura_id>/aprobar', methods=['PUT'])
@token_required
def aprobar_equivalencia(current_user, asignatura_id):
    """Aprueba una equivalencia de asignatura"""
    # En un sistema real, se verificaría si el usuario tiene permisos para esta acción
    
    updated, mensaje = AsignaturaService.aprobar_equivalencia(asignatura_id, current_user['nombre'])
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'asignatura': updated
    })

@asignaturas_bp.route('/<asignatura_id>/rechazar', methods=['PUT'])
@token_required
def rechazar_equivalencia(current_user, asignatura_id):
    """Rechaza una equivalencia de asignatura"""
    data = request.json
    
    if 'observaciones' not in data or not data['observaciones']:
        return jsonify({'message': 'Las observaciones son requeridas para rechazar una equivalencia'}), 400
    
    updated, mensaje = AsignaturaService.rechazar_equivalencia(asignatura_id, data['observaciones'], current_user['nombre'])
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'asignatura': updated
    })

@asignaturas_bp.route('/solicitud/<solicitud_id>/creditos', methods=['GET'])
@token_required
def obtener_total_creditos(current_user, solicitud_id):
    """Obtiene el total de créditos de las asignaturas aprobadas para una solicitud"""
    total_creditos, mensaje = AsignaturaService.obtener_total_creditos(solicitud_id)
    
    if total_creditos is None:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'total_creditos': total_creditos,
        'message': mensaje
    })