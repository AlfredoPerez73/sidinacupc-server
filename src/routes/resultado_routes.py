from flask import Blueprint, request, jsonify, current_app
from services.resultado_services import ResultadoService
from middlewares.auth import token_required
import os
import uuid
from werkzeug.utils import secure_filename

resultados_bp = Blueprint('resultados', __name__)

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@resultados_bp.route('/<resultado_id>', methods=['GET'])
@token_required
def get_resultado(current_user, resultado_id):
    """Obtiene un resultado por su ID"""
    resultado = ResultadoService.get_by_id(resultado_id)
    
    if not resultado:
        return jsonify({'message': 'Resultado no encontrado'}), 404
    
    return jsonify(resultado)

@resultados_bp.route('/solicitud/<solicitud_id>', methods=['GET'])
@token_required
def get_resultados_solicitud(current_user, solicitud_id):
    """Obtiene todos los resultados para una solicitud específica"""
    resultados, mensaje = ResultadoService.get_by_solicitud(solicitud_id)
    
    if not resultados:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'resultados': resultados,
        'message': mensaje
    })

@resultados_bp.route('/asignatura/<asignatura_id>', methods=['GET'])
@token_required
def get_resultado_asignatura(current_user, asignatura_id):
    """Obtiene el resultado para una asignatura específica"""
    resultado, mensaje = ResultadoService.get_by_asignatura(asignatura_id)
    
    if not resultado:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'resultado': resultado,
        'message': mensaje
    })

@resultados_bp.route('/', methods=['POST'])
@token_required
def create_resultado(current_user):
    """Crea un nuevo resultado de intercambio para una asignatura"""
    data = request.json
    
    # Validar datos requeridos
    if 'solicitud_id' not in data:
        return jsonify({'message': 'El campo solicitud_id es requerido'}), 400
    
    if 'asignatura_id' not in data:
        return jsonify({'message': 'El campo asignatura_id es requerido'}), 400
    
    if 'nota_obtenida' not in data or data['nota_obtenida'] is None:
        return jsonify({'message': 'El campo nota_obtenida es requerido'}), 400
    
    # Agregar usuario que registra el resultado
    data['registrado_por'] = current_user['nombre']
    
    resultado_id, mensaje = ResultadoService.create(data)
    
    if not resultado_id:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'resultado_id': resultado_id
    }), 201

@resultados_bp.route('/<resultado_id>', methods=['PUT'])
@token_required
def update_resultado(current_user, resultado_id):
    """Actualiza los datos de un resultado"""
    data = request.json
    
    updated, mensaje = ResultadoService.update(resultado_id, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'resultado': updated
    })

@resultados_bp.route('/<resultado_id>/documento', methods=['POST'])
@token_required
def agregar_documento_soporte(current_user, resultado_id):
    """Agrega un documento soporte a un resultado"""
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
            'tipo': request.form.get('tipo', 'certificado_notas'),
            'descripcion': request.form.get('descripcion', '')
        }
        
        # Actualizar el resultado con el documento
        resultado = ResultadoService.get_by_id(resultado_id)
        if not resultado:
            # Eliminar el archivo si hubo un error
            os.remove(file_path)
            return jsonify({'message': 'Resultado no encontrado'}), 404
        
        updated, mensaje = ResultadoService.update(resultado_id, {'documento_soporte': documento})
        
        if not updated:
            # Eliminar el archivo si hubo un error
            os.remove(file_path)
            return jsonify({'message': mensaje}), 404
        
        return jsonify({
            'message': 'Documento soporte agregado exitosamente',
            'documento': documento,
            'resultado': updated
        })
    
    return jsonify({'message': 'Tipo de archivo no permitido'}), 400

@resultados_bp.route('/<resultado_id>/aprobar', methods=['PUT'])
@token_required
def aprobar_homologacion(current_user, resultado_id):
    """Aprueba la homologación de una nota"""
    data = request.json
    
    observaciones = data.get('observaciones')
    
    updated, mensaje = ResultadoService.aprobar_homologacion(resultado_id, current_user['nombre'], observaciones)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'resultado': updated
    })

@resultados_bp.route('/<resultado_id>/rechazar', methods=['PUT'])
@token_required
def rechazar_homologacion(current_user, resultado_id):
    """Rechaza la homologación de una nota"""
    data = request.json
    
    if 'motivo' not in data or not data['motivo']:
        return jsonify({'message': 'El campo motivo es requerido para rechazar una homologación'}), 400
    
    updated, mensaje = ResultadoService.rechazar_homologacion(resultado_id, data['motivo'], current_user['nombre'])
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'resultado': updated
    })

@resultados_bp.route('/solicitud/<solicitud_id>/promedio', methods=['GET'])
@token_required
def get_promedio_intercambio(current_user, solicitud_id):
    """Calcula el promedio de las notas homologadas para una solicitud"""
    promedio, mensaje = ResultadoService.get_promedio_intercambio(solicitud_id)
    
    if promedio is None:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'promedio': promedio,
        'message': mensaje
    })