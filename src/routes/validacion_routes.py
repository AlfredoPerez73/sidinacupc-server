from flask import Blueprint, request, jsonify
from services.validacion_services import ValidacionService
from middlewares.auth import token_required

validacion_bp = Blueprint('validacion', __name__)

@validacion_bp.route('/requisitos-estudiante/<estudiante_id>', methods=['GET'])
@token_required
def validar_requisitos_estudiante(current_user, estudiante_id):
    """Valida si un estudiante cumple con los requisitos para intercambio"""
    cumple, mensaje = ValidacionService.validar_requisitos_estudiante(estudiante_id)
    
    return jsonify({
        'cumple_requisitos': cumple,
        'mensaje': mensaje
    })

@validacion_bp.route('/asignaturas-solicitud/<solicitud_id>', methods=['GET'])
@token_required
def validar_asignaturas_solicitud(current_user, solicitud_id):
    """Valida que las asignaturas de una solicitud cumplan con los requisitos mínimos"""
    cumple, mensaje = ValidacionService.validar_asignaturas_solicitud(solicitud_id)
    
    return jsonify({
        'cumple_requisitos': cumple,
        'mensaje': mensaje
    })

@validacion_bp.route('/proceso-aprobacion/<solicitud_id>/<nivel_aprobacion>', methods=['GET'])
@token_required
def validar_proceso_aprobacion(current_user, solicitud_id, nivel_aprobacion):
    """Valida si una solicitud puede avanzar al siguiente nivel de aprobación"""
    puede_avanzar, mensaje = ValidacionService.validar_proceso_aprobacion(solicitud_id, nivel_aprobacion)
    
    return jsonify({
        'puede_avanzar': puede_avanzar,
        'mensaje': mensaje
    })

@validacion_bp.route('/homologacion-resultados/<solicitud_id>', methods=['GET'])
@token_required
def validar_homologacion_resultados(current_user, solicitud_id):
    """Valida si los resultados de una solicitud pueden ser homologados"""
    puede_homologar, mensaje = ValidacionService.validar_homologacion_resultados(solicitud_id)
    
    return jsonify({
        'puede_homologar': puede_homologar,
        'mensaje': mensaje
    })

@validacion_bp.route('/finalizacion-intercambio/<solicitud_id>', methods=['GET'])
@token_required
def validar_finalizacion_intercambio(current_user, solicitud_id):
    """Valida si un intercambio puede ser finalizado"""
    puede_finalizar, mensaje = ValidacionService.validar_finalizacion_intercambio(solicitud_id)
    
    return jsonify({
        'puede_finalizar': puede_finalizar,
        'mensaje': mensaje
    })