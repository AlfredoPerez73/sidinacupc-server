from flask import Blueprint, request, jsonify
from services.convenio_services import ConvenioService
from middlewares.auth import token_required

convenios_bp = Blueprint('convenios', __name__)

@convenios_bp.route('/', methods=['GET'])
@token_required
def get_convenios(current_user):
    """Obtiene la lista de convenios"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Procesar filtros
    filters = {}
    if 'institucion' in request.args:
        filters['nombre_institucion'] = {'$regex': request.args.get('institucion'), '$options': 'i'}
    if 'pais' in request.args:
        filters['pais_institucion'] = request.args.get('pais')
    if 'tipo' in request.args:
        filters['tipo_convenio'] = request.args.get('tipo')
    if 'estado' in request.args:
        filters['estado'] = request.args.get('estado')
    
    result = ConvenioService.get_all(filters, page, per_page)
    
    return jsonify(result)

@convenios_bp.route('/importar', methods=['POST'])
@token_required
def importar_convenios(current_user):
    """Importa convenios desde un archivo CSV"""
    # Verificar permisos (solo administradores)
    if current_user['rol'] != 'admin':
        return jsonify({'message': 'No tiene permisos para realizar esta acción'}), 403
    
    # Verificar archivo
    if 'convenios' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    file = request.files['convenios']
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = ConvenioService.importar_csv(file)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'convenios_creados': result['convenios_creados'],
        'errores': result['errores']
    })

@convenios_bp.route('/<convenio_id>', methods=['GET'])
@token_required
def get_convenio(current_user, convenio_id):
    """Obtiene un convenio por su ID"""
    convenio = ConvenioService.get_by_id(convenio_id)
    
    if not convenio:
        return jsonify({'message': 'Convenio no encontrado'}), 404
    
    return jsonify(convenio)

@convenios_bp.route('/', methods=['POST'])
@token_required
def create_convenio(current_user):
    """Crea un nuevo convenio"""
    data = request.json
    
    # Validar datos requeridos
    required_fields = ['nombre_institucion', 'pais_institucion', 'ciudad_institucion', 
                        'tipo_convenio', 'fecha_inicio', 'fecha_fin']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'El campo {field} es requerido'}), 400
    
    convenio_id, mensaje = ConvenioService.create(data)
    
    return jsonify({
        'message': mensaje,
        'convenio_id': convenio_id
    }), 201

@convenios_bp.route('/<convenio_id>', methods=['PUT'])
@token_required
def update_convenio(current_user, convenio_id):
    """Actualiza un convenio existente"""
    data = request.json
    
    updated, mensaje = ConvenioService.update(convenio_id, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'convenio': updated
    })

@convenios_bp.route('/<convenio_id>', methods=['DELETE'])
@token_required
def delete_convenio(current_user, convenio_id):
    """Elimina un convenio (cambio de estado a inactivo)"""
    success, mensaje = ConvenioService.delete(convenio_id)
    
    if not success:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje
    })

@convenios_bp.route('/activos', methods=['GET'])
@token_required
def get_convenios_activos(current_user):
    """Obtiene todos los convenios activos"""
    convenios = ConvenioService.get_activos()
    
    return jsonify({
        'convenios': convenios
    })

@convenios_bp.route('/buscar-por-institucion/<nombre_institucion>', methods=['GET'])
@token_required
def buscar_por_institucion(current_user, nombre_institucion):
    """Busca convenios por nombre de institución"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    result = ConvenioService.buscar_por_institucion(nombre_institucion, page, per_page)
    
    return jsonify(result)

@convenios_bp.route('/buscar-por-pais/<pais>', methods=['GET'])
@token_required
def buscar_por_pais(current_user, pais):
    """Busca convenios por país"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    result = ConvenioService.buscar_por_pais(pais, page, per_page)
    
    return jsonify(result)

@convenios_bp.route('/buscar-por-tipo/<tipo_convenio>', methods=['GET'])
@token_required
def buscar_por_tipo(current_user, tipo_convenio):
    """Busca convenios por tipo (nacional/internacional)"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    result = ConvenioService.buscar_por_tipo(tipo_convenio, page, per_page)
    
    return jsonify(result)