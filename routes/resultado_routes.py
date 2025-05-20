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

@resultados_bp.route('/importar', methods=['POST'])
@token_required
def importar_resultados(current_user):
    """Importa resultados desde un archivo CSV"""
    # Verificar permisos
    if current_user['rol'] not in ['admin', 'orpi']:
        return jsonify({'message': 'No tiene permisos para realizar esta acción'}), 403
    
    # Verificar archivo
    if 'file' not in request.files:
        return jsonify({'message': 'No se encontró el archivo'}), 400
    
    # Verificar id_solicitud en formulario
    if 'id_solicitud' not in request.form:
        return jsonify({'message': 'Se requiere el ID de la solicitud'}), 400
    
    id_solicitud = request.form['id_solicitud']
    file = request.files['file']
    
    # Obtener escala de origen (opcional)
    escala_origen = request.form.get('escala_origen', '0-10')
    
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'message': 'Archivo no válido. Debe ser un CSV'}), 400
    
    # Procesar archivo
    result, message = ResultadoService.importar_csv(file, id_solicitud, escala_origen)
    
    if not result:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'total_importados': result['total_importados'],
        'resultados_creados': result['resultados_creados'],
        'errores': result['errores']
    })

@resultados_bp.route('/<id_resultado>', methods=['GET'])
@token_required
def get_resultado(current_user, id_resultado):
    """Obtiene un resultado por su ID"""
    resultado = ResultadoService.get_by_id(id_resultado)
    
    if not resultado:
        return jsonify({'message': 'Resultado no encontrado'}), 404
    
    return jsonify(resultado)

@resultados_bp.route('/solicitud/<id_solicitud>', methods=['GET'])
@token_required
def get_resultados_solicitud(current_user, id_solicitud):
    """Obtiene todos los resultados para una solicitud específica"""
    resultados, mensaje = ResultadoService.get_by_solicitud(id_solicitud)
    
    if not resultados:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'resultados': resultados,
        'message': mensaje
    })

@resultados_bp.route('/asignatura/<id_asignatura>', methods=['GET'])
@token_required
def get_resultado_asignatura(current_user, id_asignatura):
    """Obtiene el resultado para una asignatura específica"""
    resultado, mensaje = ResultadoService.get_by_asignatura(id_asignatura)
    
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
    if 'id_solicitud' not in data:
        return jsonify({'message': 'El campo id_solicitud es requerido'}), 400
    
    if 'id_asignatura' not in data:
        return jsonify({'message': 'El campo id_asignatura es requerido'}), 400
    
    if 'nota_obtenida' not in data or data['nota_obtenida'] is None:
        return jsonify({'message': 'El campo nota_obtenida es requerido'}), 400
    
    # Agregar usuario que registra el resultado
    data['registrado_por'] = current_user['nombre']
    
    id_resultado, mensaje = ResultadoService.create(data)
    
    if not id_resultado:
        return jsonify({'message': mensaje}), 400
    
    return jsonify({
        'message': mensaje,
        'id_resultado': id_resultado
    }), 201

@resultados_bp.route('/<id_resultado>', methods=['PUT'])
@token_required
def update_resultado(current_user, id_resultado):
    """Actualiza los datos de un resultado"""
    data = request.json
    
    updated, mensaje = ResultadoService.update(id_resultado, data)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'resultado': updated
    })

@resultados_bp.route('/<id_resultado>/documento', methods=['POST'])
@token_required
def agregar_documento_soporte(current_user, id_resultado):
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
        resultado = ResultadoService.get_by_id(id_resultado)
        if not resultado:
            # Eliminar el archivo si hubo un error
            os.remove(file_path)
            return jsonify({'message': 'Resultado no encontrado'}), 404
        
        updated, mensaje = ResultadoService.update(id_resultado, {'documento_soporte': documento})
        
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

@resultados_bp.route('/<id_resultado>/aprobar', methods=['PUT'])
@token_required
def aprobar_homologacion(current_user, id_resultado):
    """Aprueba la homologación de una nota"""
    data = request.json
    
    observaciones = data.get('observaciones')
    
    updated, mensaje = ResultadoService.aprobar_homologacion(id_resultado, current_user['nombre'], observaciones)
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'resultado': updated
    })

@resultados_bp.route('/<id_resultado>/rechazar', methods=['PUT'])
@token_required
def rechazar_homologacion(current_user, id_resultado):
    """Rechaza la homologación de una nota"""
    data = request.json
    
    if 'motivo' not in data or not data['motivo']:
        return jsonify({'message': 'El campo motivo es requerido para rechazar una homologación'}), 400
    
    updated, mensaje = ResultadoService.rechazar_homologacion(id_resultado, data['motivo'], current_user['nombre'])
    
    if not updated:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'message': mensaje,
        'resultado': updated
    })

@resultados_bp.route('/solicitud/<id_solicitud>/promedio', methods=['GET'])
@token_required
def get_promedio_intercambio(current_user, id_solicitud):
    """Calcula el promedio de las notas homologadas para una solicitud"""
    promedio, mensaje = ResultadoService.get_promedio_intercambio(id_solicitud)
    
    if promedio is None:
        return jsonify({'message': mensaje}), 404
    
    return jsonify({
        'promedio': promedio,
        'message': mensaje
    })