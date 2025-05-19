from flask import Blueprint, request, jsonify, current_app
from models.solicitud import Solicitud
from models.estudiante import Estudiante
from models.docente import Docente  # Asumiendo que existe un modelo de Docente
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
    if 'id_solicitante' in request.args:
        filters['id_solicitante'] = ObjectId(request.args.get('id_solicitante'))
    if 'tipo_solicitante' in request.args:
        filters['tipo_solicitante'] = request.args.get('tipo_solicitante')
    
    result = Solicitud.get_all(filters, page, per_page)
    
    # Enriquecer las solicitudes con datos de solicitantes y convenios
    solicitudes_enriquecidas = []
    for solicitud in result['solicitudes']:
        solicitud_dict = serialize_doc(solicitud)
        
        # Agregar información del solicitante (estudiante o docente)
        if solicitud.get('tipo_solicitante') == 'docente':
            solicitante = Docente.get_by_id(str(solicitud['id_solicitante']))
            if solicitante:
                solicitud_dict['solicitante'] = {
                    'nombre': solicitante.get('nombre_completo'),
                    'departamento': solicitante.get('departamento'),
                    'facultad': solicitante.get('facultad'),
                    'tipo': 'docente'
                }
        else:  # Por defecto es estudiante
            solicitante = Estudiante.get_by_id(str(solicitud['id_solicitante']))
            if solicitante:
                solicitud_dict['solicitante'] = {
                    'nombre': solicitante.get('nombre_completo'),
                    'programa': solicitante.get('programa_academico'),
                    'facultad': solicitante.get('facultad'),
                    'tipo': 'estudiante'
                }
        
        # Agregar información del convenio
        convenio = Convenio.get_by_id(str(solicitud['id_convenio']))
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

@solicitudes_bp.route('/<id_solicitud>', methods=['GET'])
@token_required
def get_solicitud(current_user, id_solicitud):
    """Obtiene una solicitud por su ID"""
    solicitud = Solicitud.get_by_id(id_solicitud)
    
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    solicitud_dict = serialize_doc(solicitud)
    
    # Agregar información del solicitante (estudiante o docente)
    if solicitud.get('tipo_solicitante') == 'docente':
        solicitante = Docente.get_by_id(str(solicitud['id_solicitante']))
        if solicitante:
            solicitud_dict['solicitante'] = serialize_doc(solicitante)
            solicitud_dict['solicitante']['tipo'] = 'docente'
    else:  # Por defecto es estudiante
        solicitante = Estudiante.get_by_id(str(solicitud['id_solicitante']))
        if solicitante:
            solicitud_dict['solicitante'] = serialize_doc(solicitante)
            solicitud_dict['solicitante']['tipo'] = 'estudiante'
    
    # Agregar información del convenio
    convenio = Convenio.get_by_id(str(solicitud['id_convenio']))
    if convenio:
        solicitud_dict['convenio'] = serialize_doc(convenio)
    
    return jsonify(solicitud_dict)

@solicitudes_bp.route('/', methods=['POST'])
@token_required
def create_solicitud(current_user):
    """Crea una nueva solicitud de intercambio"""
    data = request.json
    
    # Validar datos requeridos
    required_fields = ['id_solicitante', 'id_convenio', 'periodo_academico', 
                       'modalidad', 'tipo_intercambio', 'duracion']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'El campo {field} es requerido'}), 400
    
    # Verificar tipo de solicitante
    tipo_solicitante = data.get('tipo_solicitante', 'estudiante')
    
    # Verificar que el solicitante exista
    if tipo_solicitante == 'docente':
        solicitante = Docente.get_by_id(data['id_solicitante'])
        if not solicitante:
            return jsonify({'message': 'Docente no encontrado'}), 404
        
        # Verificar requisitos para docentes si es necesario
        # (implementar lógica específica para docentes)
    else:
        # Por defecto verificamos que sea un estudiante
        solicitante = Estudiante.get_by_id(data['id_solicitante'])
        if not solicitante:
            return jsonify({'message': 'Estudiante no encontrado'}), 404
        
        # Verificar que el estudiante cumpla con los requisitos
        cumple, mensaje = Estudiante.cumple_requisitos_intercambio(data['id_solicitante'])
        if not cumple:
            return jsonify({
                'message': f'El estudiante no cumple con los requisitos: {mensaje}'
            }), 400
    
    # Verificar que el convenio exista
    convenio = Convenio.get_by_id(data['id_convenio'])
    if not convenio:
        return jsonify({'message': 'Convenio no encontrado'}), 404
    
    # Crear la solicitud
    id_solicitud = Solicitud.create(data)
    
    return jsonify({
        'message': 'Solicitud creada exitosamente',
        'id_solicitud': id_solicitud
    }), 201

@solicitudes_bp.route('/<id_solicitud>', methods=['PUT'])
@token_required
def update_solicitud(current_user, id_solicitud):
    """Actualiza una solicitud existente"""
    data = request.json
    
    solicitud = Solicitud.get_by_id(id_solicitud)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated = Solicitud.update(id_solicitud, data)
    
    return jsonify({
        'message': 'Solicitud actualizada exitosamente',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<id_solicitud>/estado', methods=['PUT'])
@token_required
def update_estado_solicitud(current_user, id_solicitud):
    """Actualiza el estado de una solicitud"""
    data = request.json
    
    if 'estado' not in data:
        return jsonify({'message': 'El campo estado es requerido'}), 400
    
    solicitud = Solicitud.get_by_id(id_solicitud)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    comentarios = data.get('comentarios')
    
    updated = Solicitud.update_estado(id_solicitud, data['estado'], comentarios)
    
    return jsonify({
        'message': f'Estado de solicitud actualizado a {data["estado"]}',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<id_solicitud>/aprobacion/jefe-programa', methods=['PUT'])
@token_required
def aprobar_jefe_programa(current_user, id_solicitud):
    """Aprueba una solicitud por parte del jefe de programa"""
    solicitud = Solicitud.get_by_id(id_solicitud)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated = Solicitud.aprobar_jefe_programa(id_solicitud)
    
    return jsonify({
        'message': 'Solicitud aprobada por el jefe de programa',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<id_solicitud>/aprobacion/consejo-facultad', methods=['PUT'])
@token_required
def aprobar_consejo_facultad(current_user, id_solicitud):
    """Aprueba una solicitud por parte del consejo de facultad"""
    solicitud = Solicitud.get_by_id(id_solicitud)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated = Solicitud.aprobar_consejo_facultad(id_solicitud)
    
    return jsonify({
        'message': 'Solicitud aprobada por el consejo de facultad',
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<id_solicitud>/aprobacion/orpi', methods=['PUT'])
@token_required
def aprobar_ORPI(current_user, id_solicitud):
    """Aprueba una solicitud por parte de la oficina de ORPI"""
    solicitud = Solicitud.get_by_id(id_solicitud)
    if not solicitud:
        return jsonify({'message': 'Solicitud no encontrada'}), 404
    
    updated, mensaje = Solicitud.aprobar_ORPI(id_solicitud)
    
    if not updated:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'solicitud': serialize_doc(updated)
    })

@solicitudes_bp.route('/<id_solicitud>/documentos', methods=['POST'])
@token_required
def upload_documento(current_user, id_solicitud):
    """Sube un documento para una solicitud"""
    solicitud = Solicitud.get_by_id(id_solicitud)
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
        
        updated = Solicitud.agregar_documento(id_solicitud, documento)
        
        return jsonify({
            'message': 'Documento subido exitosamente',
            'documento': documento,
            'solicitud': serialize_doc(updated)
        })
    
    return jsonify({'message': 'Tipo de archivo no permitido'}), 400