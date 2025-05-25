from flask import Blueprint, request, jsonify
from services.docente_services import DocenteService
from middlewares.auth import token_required
import logging

logger = logging.getLogger(__name__)

docente_bp = Blueprint('docentes', __name__)

@docente_bp.route('/', methods=['POST'])
@token_required
def crear_docente(current_user):
    """Endpoint para crear un nuevo docente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron datos',
                'data': None
            }), 400
        
        result = DocenteService.crear_docente(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint crear_docente: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/importar', methods=['POST'])
@token_required
def importar_csv(current_user):
    """Endpoint para importar docentes desde CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó archivo',
                'data': None
            }), 400
        
        file = request.files['docentes']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No se seleccionó archivo',
                'data': None
            }), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'message': 'El archivo debe ser de formato CSV',
                'data': None
            }), 400
        
        result = DocenteService.importar_csv(file)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint importar_csv: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/', methods=['GET'])
@token_required
def listar_docentes(current_user):
    """Endpoint para listar docentes con paginación y filtros"""
    try:
        # Obtener parámetros de consulta
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Construir filtros
        filters = {}
        
        if request.args.get('estado'):
            filters['estado'] = request.args.get('estado')
        
        if request.args.get('departamento'):
            filters['departamento'] = request.args.get('departamento')
        
        if request.args.get('facultad'):
            filters['facultad'] = request.args.get('facultad')
        
        if request.args.get('categoria_docente'):
            filters['categoria_docente'] = request.args.get('categoria_docente')
        
        if request.args.get('tipo_vinculacion'):
            filters['tipo_vinculacion'] = request.args.get('tipo_vinculacion')
        
        if request.args.get('nombre'):
            filters['nombre'] = request.args.get('nombre')
        
        result = DocenteService.listar_docentes(page, per_page, filters)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': 'Parámetros de paginación inválidos',
            'data': None
        }), 400
    except Exception as e:
        logger.error(f"Error en endpoint listar_docentes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/<id_docente>', methods=['GET'])
@token_required
def obtener_docente(current_user, id_docente):
    """Endpoint para obtener un docente por ID"""
    try:
        result = DocenteService.obtener_docente(id_docente)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error en endpoint obtener_docente: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/<id_docente>', methods=['PUT'])
@token_required
def actualizar_docente(current_user, id_docente):
    """Endpoint para actualizar un docente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron datos',
                'data': None
            }), 400
        
        result = DocenteService.actualizar_docente(id_docente, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint actualizar_docente: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/<id_docente>', methods=['DELETE'])
@token_required
def eliminar_docente(current_user, id_docente):
    """Endpoint para eliminar (inactivar) un docente"""
    try:
        result = DocenteService.eliminar_docente(id_docente)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error en endpoint eliminar_docente: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/documento/<documento>', methods=['GET'])
@token_required
def obtener_por_documento(current_user, documento):
    """Endpoint para obtener un docente por documento de identidad"""
    try:
        result = DocenteService.obtener_por_documento(documento)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error en endpoint obtener_por_documento: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/buscar', methods=['GET'])
@token_required
def buscar_por_nombre(current_user):
    """Endpoint para buscar docentes por nombre"""
    try:
        nombre = request.args.get('nombre')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if not nombre:
            return jsonify({
                'success': False,
                'message': 'El parámetro nombre es requerido',
                'data': None
            }), 400
        
        result = DocenteService.buscar_por_nombre(nombre, page, per_page)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': 'Parámetros de paginación inválidos',
            'data': None
        }), 400
    except Exception as e:
        logger.error(f"Error en endpoint buscar_por_nombre: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/departamento/<departamento>', methods=['GET'])
@token_required
def obtener_por_departamento(current_user, departamento):
    """Endpoint para obtener docentes por departamento"""
    try:
        result = DocenteService.obtener_por_departamento(departamento)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint obtener_por_departamento: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/estadisticas', methods=['GET'])
@token_required
def obtener_estadisticas(current_user):
    """Endpoint para obtener estadísticas de docentes"""
    try:
        result = DocenteService.obtener_estadisticas()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint obtener_estadisticas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/<id_docente>/requisitos-intercambio', methods=['GET'])
@token_required
def verificar_requisitos_intercambio(current_user, id_docente):
    """Endpoint para verificar si un docente cumple requisitos de intercambio"""
    try:
        result = DocenteService.verificar_requisitos_intercambio(id_docente)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint verificar_requisitos_intercambio: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/elegibles-intercambio', methods=['GET'])
@token_required
def obtener_docentes_elegibles(current_user):
    """Endpoint para obtener docentes elegibles para intercambio"""
    try:
        result = DocenteService.obtener_docentes_elegibles()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint obtener_docentes_elegibles: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

@docente_bp.route('/<id_docente>/experiencia-internacional', methods=['POST'])
@token_required
def registrar_experiencia_internacional(current_user, id_docente):
    """Endpoint para registrar experiencia internacional de un docente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron datos',
                'data': None
            }), 400
        
        result = DocenteService.registrar_experiencia_internacional(id_docente, data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en endpoint registrar_experiencia_internacional: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'data': None
        }), 500

# Error handlers específicos para el blueprint
@docente_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Recurso no encontrado',
        'data': None
    }), 404

@docente_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Error interno del servidor',
        'data': None
    }), 500