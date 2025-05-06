from flask import Blueprint, request, jsonify, current_app
from models.solicitud import Solicitud
from models.estudiante import Estudiante
from services.solicitud_services import SolicitudService
from models.convenio import Convenio
from db.db import serialize_doc
from middlewares.auth import token_required
from bson import ObjectId
import os
import uuid
from werkzeug.utils import secure_filename

solicitudes_bp = Blueprint('solicitudes', __name__)

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@solicitudes_bp.route('/importar', methods=['POST'])
@token_required
def importar_solicitudes(current_user):
    """Importa solicitudes desde un archivo CSV"""
    # Verificar permisos (administradores o coordinadores ORPI)
    if current_user['rol'] not in ['admin', 'orpi']:
        return jsonify({'message': 'No tiene permisos para realizar esta acción'}), 403
    
    # Verificar archivo
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = SolicitudService.importar_csv(file)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'solicitudes_creadas': result['solicitudes_creados'],
        'errores': result['errores']
    })

@solicitudes_bp.route('/', methods=['GET'])
@token_required
def get_solicitudes(current_user):
    """Obtiene la lista de solicitudes de intercambio"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Procesar filtros
    filters = {}
    if 'estado' in request.args:
        filters['estado_solicitud'] = request.args.get('estado')
    if 'tipo' in request.args:
        filters['tipo_intercambio'] = request.args.get('tipo')
    if 'periodo' in request.args:
        filters['periodo_academico'] = request.args.get('periodo')
    if 'estudiante_id' in request.args:
        filters['estudiante_id'] = ObjectId(request.args.get('estudiante_id'))
    
    result = Solicitud.get_all(filters, page, per_page)
    
    # Enriquecer las solicitudes con datos de estudiantes y convenios
    solicitudes_enriquecidas = []
    for solicitud in result['solicitudes']:
        solicitud_dict = serialize_doc(solicitud)
        
        # Agregar información del estudiante
        estudiante = Estudiante.get_by_id(str(solicitud['estudiante_id']))
        if estudiante:
            solicitud_dict['estudiante'] = {
                'nombre': estudiante.get('nombre_completo'),
                'programa': estudiante.get('programa_academico'),
                'facultad': estudiante.get('facultad')
            }
        
        # Agregar información del convenio
        convenio = Convenio.get_by_id(str(solicitud['convenio_id']))
        if convenio:
            solicitud_dict['convenio'] = {
                'nombre_institucion': convenio.get('nombre_institucion'),
                'pais': convenio.get('pais_institucion'),
                'tipo': convenio.get('tipo_convenio')
            }
        
        solicitudes_enriquecidas.append(solicitud_dict)
    
    return jsonify({
        'solicitudes': solicitudes_enriquecidas,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages']
    })

@solicitudes_bp.route('/<solicitud_id>', methods=['GET'])
@token_required
def get_solicitud(current_user, solicitud_id):
    """Obtiene una solicitud por su ID"""
    solicitud = Solicitud.get_by_id(solicitud_id)
    
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    solicitud_dict = serialize_doc(solicitud)
    
    # Agregar información del estudiante
    estudiante = Estudiante.get_by_id(str(solicitud['estudiante_id']))
    if estudiante:
        solicitud_dict['estudiante'] = serialize_doc(estudiante)
    
    # Agregar información del convenio
    convenio = Convenio.get_by_id(str(solicitud['convenio_id']))
    if convenio:
        solicitud_dict['convenio'] = serialize_doc(convenio)
    
    return jsonify(solicitud_dict)

@solicitudes_bp.route('/', methods=['POST'])
@token_required
def create_solicitud(current_user):
    """Crea una nueva solicitud de intercambio"""
    data = request.json
    
    # Validar datos requeridos
    required_fields = ['estudiante_id', 'convenio_id', 'periodo_academico', 
                       'modalidad', 'tipo_intercambio', 'duracion']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'El campo {field} es requerido'}), 400
    
    # Verificar que el estudiante exista
    estudiante = Estudiante.get_by_id(data['estudiante_id'])
    if not estudiante:
        return jsonify({'message': 'Estudiante no encontrado'}), 404
    
    # Verificar que el convenio exista
    convenio = Convenio.get_by_id(data['convenio_id'])
    if not convenio:
        return jsonify({'message': 'Convenio no encontrado'}), 404
    
    # Verificar que el estudiante cumpla con los requisitos
    cumple, mensaje = Estudiante.cumple_requisitos_intercambio(data['estudiante_id'])
    if not cumple:
        return jsonify({
            'message': f'El estudiante no cumple con los requisitos: {mensaje}'
        }), 400
    
    # Crear la solicitud
    solicitud_id = Solicitud.create(data)
    
    return jsonify({
        'message': 'Solicitud creada exitosamente',
        'solicitud_id': solicitud_id
    }), 201

@solicitudes_bp.route('/<solicitud_id>', methods=['PUT'])
@token_required
def update_solicitud(current_user, solicitud_id):
    """Actualiza una solicitud existente"""
    data = request.json
    
    solicitud = Solicitud.get_by_id(solicitud_id)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated = Solicitud.update(solicitud_id, data)
    
    return jsonify({
        'message': 'Solicitud actualizada exitosamente',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<solicitud_id>/estado', methods=['PUT'])
@token_required
def update_estado_solicitud(current_user, solicitud_id):
    """Actualiza el estado de una solicitud"""
    data = request.json
    
    if 'estado' not in data:
        return jsonify({'message': 'El campo estado es requerido'}), 400
    
    solicitud = Solicitud.get_by_id(solicitud_id)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    comentarios = data.get('comentarios')
    
    updated = Solicitud.update_estado(solicitud_id, data['estado'], comentarios)
    
    return jsonify({
        'message': f'Estado de solicitud actualizado a {data["estado"]}',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<solicitud_id>/aprobacion/jefe-programa', methods=['PUT'])
@token_required
def aprobar_jefe_programa(current_user, solicitud_id):
    """Aprueba una solicitud por parte del jefe de programa"""
    solicitud = Solicitud.get_by_id(solicitud_id)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated = Solicitud.aprobar_jefe_programa(solicitud_id)
    
    return jsonify({
        'message': 'Solicitud aprobada por el jefe de programa',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<solicitud_id>/aprobacion/consejo-facultad', methods=['PUT'])
@token_required
def aprobar_consejo_facultad(current_user, solicitud_id):
    """Aprueba una solicitud por parte del consejo de facultad"""
    solicitud = Solicitud.get_by_id(solicitud_id)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated = Solicitud.aprobar_consejo_facultad(solicitud_id)
    
    return jsonify({
        'message': 'Solicitud aprobada por el consejo de facultad',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<solicitud_id>/aprobacion/orpi', methods=['PUT'])
@token_required
def aprobar_ORPI(current_user, solicitud_id):
    """Aprueba una solicitud por parte de la oficina de ORPI"""
    solicitud = Solicitud.get_by_id(solicitud_id)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated, mensaje = Solicitud.aprobar_ORPI(solicitud_id)
    
    if not updated:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<solicitud_id>/documentos', methods=['POST'])
@token_required
def upload_documento(current_user, solicitud_id):
    """Sube un documento para una solicitud"""
    solicitud = Solicitud.get_by_id(solicitud_id)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
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
            'descripcion': request.form.get('descripcion', '')
        }
        
        updated = Solicitud.agregar_documento(solicitud_id, documento)
        
        return jsonify({
            'message': 'Documento subido exitosamente',
            'documento': documento,
            'solicitud': serialize_doc(updated)
        })
    
    return jsonify({'message': 'Tipo de archivo no permitido'}), 400