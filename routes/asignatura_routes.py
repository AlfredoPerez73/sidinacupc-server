from flask import Blueprint, request, jsonify
from services.asignatura_services import AsignaturaService
from middlewares.auth import token_required

asignaturas_bp = Blueprint('asignaturas', __name__)

@asignaturas_bp.route('/<id_asignatura>', methods=['GET'])
@token_required
def get_asignatura(current_user, id_asignatura):
    """Obtiene una asignatura por su ID"""
    asignatura = AsignaturaService.get_by_id(id_asignatura)
    
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
    
    # Verificar id_solicitud en formulario
    if 'id_solicitud' not in request.form:
        return jsonify({'message': 'Se requiere el ID de la solicitud'}), 400
    
    id_solicitud = request.form['id_solicitud']
    file = request.files['file']
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = AsignaturaService.importar_csv(file, id_solicitud)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'asignaturas_creadas': result['asignaturas_creadas'],
        'errores': result['errores']
    })

@asignaturas_bp.route('/solicitud/<id_solicitud>', methods=['GET'])
@token_required
def get_asignaturas_solicitud(current_user, id_solicitud):
    """Obtiene todas las asignaturas para una solicitud específica"""
    asignaturas, mensaje = AsignaturaService.get_by_solicitud(id_solicitud)
    
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
    if 'id_solicitud' not in data:
        return jsonify({'message': 'El campo id_solicitud es requerido'}), 400
    
    id_asignatura, mensaje = AsignaturaService.create(data)
    
    if not id_asignatura:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'id_asignatura': id_asignatura
    }), 201

@asignaturas_bp.route('/<id_asignatura>', methods=['PUT'])
@token_required
def update_asignatura(current_user, id_asignatura):
    """Actualiza los datos de una asignatura"""
    data = request.json
    
    updated, mensaje = AsignaturaService.update(id_asignatura, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'asignatura': updated
    })

@asignaturas_bp.route('/<id_asignatura>', methods=['DELETE'])
@token_required
def delete_asignatura(current_user, id_asignatura):
    """Elimina una asignatura"""
    success, mensaje = AsignaturaService.delete(id_asignatura)
    
    if not success:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje
    })

@asignaturas_bp.route('/<id_asignatura>/aprobar', methods=['PUT'])
@token_required
def aprobar_equivalencia(current_user, id_asignatura):
    """Aprueba una equivalencia de asignatura"""
    # En un sistema real, se verificaría si el usuario tiene permisos para esta acción
    
    updated, mensaje = AsignaturaService.aprobar_equivalencia(id_asignatura, current_user['nombre'])
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'asignatura': updated
    })

@asignaturas_bp.route('/<id_asignatura>/rechazar', methods=['PUT'])
@token_required
def rechazar_equivalencia(current_user, id_asignatura):
    """Rechaza una equivalencia de asignatura"""
    data = request.json
    
    if 'observaciones' not in data or not data['observaciones']:
        return jsonify({'message': 'Las observaciones son requeridas para rechazar una equivalencia'}), 400
    
    updated, mensaje = AsignaturaService.rechazar_equivalencia(id_asignatura, data['observaciones'], current_user['nombre'])
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'asignatura': updated
    })

@asignaturas_bp.route('/solicitud/<id_solicitud>/creditos', methods=['GET'])
@token_required
def obtener_total_creditos(current_user, id_solicitud):
    """Obtiene el total de créditos de las asignaturas aprobadas para una solicitud"""
    total_creditos, mensaje = AsignaturaService.obtener_total_creditos(id_solicitud)
    
    if total_creditos is None:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'total_creditos': total_creditos,
        'message': mensaje
    })