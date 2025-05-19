from flask import Blueprint, request, jsonify, current_app
from services.seguimiento_services import SeguimientoService
from middlewares.auth import token_required
import os
import uuid
from werkzeug.utils import secure_filename
from models.estudiante import Estudiante
from models.solicitud import Solicitud
from models.convenio import Convenio
from bson import ObjectId

seguimiento_bp = Blueprint('seguimiento', __name__)

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@seguimiento_bp.route('/importarReportes', methods=['POST'])
@token_required
def importar_reportes(current_user):
    """Importa reportes de seguimiento desde un archivo CSV"""
    # Verificar permisos
    if current_user['rol'] not in ['admin', 'orpi']:
        return jsonify({'message': 'No tiene permisos para realizar esta acción'}), 403
    
    # Verificar archivo
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    # Verificar id_seguimiento en formulario
    if 'id_seguimiento' not in request.form:
        return jsonify({'message': 'Se requiere el ID del seguimiento'}), 400
    
    id_seguimiento = request.form['id_seguimiento']
    file = request.files['file']
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = SeguimientoService.importar_reportes_csv(file, id_seguimiento)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'reportes_creados': result['reportes_creados'],
        'errores': result['errores']
    })

@seguimiento_bp.route('/<id_seguimiento>', methods=['GET'])
@token_required
def get_seguimiento(current_user, id_seguimiento):
    """Obtiene un seguimiento por su ID"""
    seguimiento = SeguimientoService.get_by_id(id_seguimiento)
    
    if not seguimiento:
        return jsonify({'message': 'Seguimiento no encontrado'}), 404
    
    return jsonify(seguimiento)

@seguimiento_bp.route('/solicitud/<id_solicitud>', methods=['GET'])
@token_required
def get_seguimiento_solicitud(current_user, id_solicitud):
    """Obtiene el seguimiento para una solicitud específica"""
    seguimiento, mensaje = SeguimientoService.get_by_solicitud(id_solicitud)
    
    if not seguimiento:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'seguimiento': seguimiento,
        'message': mensaje
    })

@seguimiento_bp.route('/', methods=['POST'])
@token_required
def create_seguimiento(current_user):
    """Crea un nuevo seguimiento para una solicitud"""
    data = request.json
    
    # Validar datos requeridos
    if 'id_solicitud' not in data:
        return jsonify({'message': 'El campo id_solicitud es requerido'}), 400
    
    id_seguimiento, mensaje = SeguimientoService.create(data)
    
    if not id_seguimiento:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'id_seguimiento': id_seguimiento
    }), 201

@seguimiento_bp.route('/<id_seguimiento>', methods=['PUT'])
@token_required
def update_seguimiento(current_user, id_seguimiento):
    """Actualiza los datos de un seguimiento"""
    data = request.json
    
    updated, mensaje = SeguimientoService.update(id_seguimiento, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'seguimiento': updated
    })

@seguimiento_bp.route('/<id_seguimiento>/reporte', methods=['POST'])
@token_required
def agregar_reporte(current_user, id_seguimiento):
    """Agrega un nuevo reporte de avance al seguimiento"""
    data = request.json
    
    # Validar datos requeridos
    if 'contenido' not in data or not data['contenido']:
        return jsonify({'message': 'El campo contenido es requerido'}), 400
    
    # Agregar información del usuario que reporta
    data['usuario'] = current_user['nombre']
    
    updated, mensaje = SeguimientoService.agregar_reporte(id_seguimiento, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'seguimiento': updated
    })

@seguimiento_bp.route('/<id_seguimiento>/documento', methods=['POST'])
@token_required
def agregar_documento(current_user, id_seguimiento):
    """Agrega un nuevo documento soporte al seguimiento"""
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400
    
    if file and allowed_file(file.filename):
        # Generar nombre único para el archivo
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        file.save(file_path)
        
        documento = {
            'nombre': secure_filename(file.filename),
            'archivo': filename,
            'ruta': file_path,
            'tipo': request.form.get('tipo', 'documento'),
            'descripcion': request.form.get('descripcion', ''),
            'usuario': current_user['nombre']
        }
        
        updated, mensaje = SeguimientoService.agregar_documento(id_seguimiento, documento)
        
        if not updated:
            # Eliminar el archivo si hubo un error
            os.remove(file_path)
            return jsonify({'message': mensaje}), 404
        
        return jsonify({
            'message': mensaje,
            'documento': documento,
            'seguimiento': updated
        })
    
    return jsonify({'message': 'Tipo de archivo no permitido'}), 400

@seguimiento_bp.route('/<id_seguimiento>/evaluacion', methods=['POST'])
@token_required
def agregar_evaluacion(current_user, id_seguimiento):
    """Agrega una nueva evaluación al seguimiento"""
    data = request.json
    
    # Validar datos requeridos
    if 'calificacion' not in data or data['calificacion'] is None:
        return jsonify({'message': 'El campo calificación es requerido'}), 400
    
    if 'comentarios' not in data or not data['comentarios']:
        return jsonify({'message': 'El campo comentarios es requerido'}), 400
    
    # Agregar información del usuario que evalúa
    data['usuario'] = current_user['nombre']
    
    updated, mensaje = SeguimientoService.agregar_evaluacion(id_seguimiento, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'seguimiento': updated
    })

@seguimiento_bp.route('/<id_seguimiento>/estado', methods=['PUT'])
@token_required
def cambiar_estado(current_user, id_seguimiento):
    """Cambia el estado actual del seguimiento"""
    data = request.json
    
    if 'estado' not in data:
        return jsonify({'message': 'El campo estado es requerido'}), 400
    
    updated, mensaje = SeguimientoService.cambiar_estado(id_seguimiento, data['estado'], data.get('observaciones'))
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'seguimiento': updated
    })

@seguimiento_bp.route('/activos', methods=['GET'])
@token_required
def get_seguimientos_activos(current_user):
    """Obtiene todos los seguimientos activos (en proceso)"""
    seguimientos = SeguimientoService.get_all_active()
    
    return jsonify({
        'seguimientos': seguimientos,
        'total': len(seguimientos)
    })

@seguimiento_bp.route('/filtrar', methods=['GET'])
@token_required
def filtrar_seguimientos(current_user):
    """Obtiene seguimientos con filtros y paginación"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Procesar filtros
    filters = {}
    if 'estado' in request.args:
        filters['estado_actual'] = request.args.get('estado')
    
    result = SeguimientoService.get_by_filters(filters, page, per_page)
    
    return jsonify(result)