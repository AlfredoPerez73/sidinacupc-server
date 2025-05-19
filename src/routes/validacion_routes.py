from flask import Blueprint, request, jsonify
from services.validacion_services import ValidacionService
from middlewares.auth import token_required

validacion_bp = Blueprint('validacion', __name__)

@validacion_bp.route('/requisitos-estudiante/<id_estudiante>', methods=['GET'])
@token_required
def validar_requisitos_estudiante(current_user, id_estudiante):
    """Valida si un estudiante cumple con los requisitos para intercambio"""
    cumple, mensaje = ValidacionService.validar_requisitos_estudiante(id_estudiante)
    
    return jsonify({
        'cumple_requisitos': cumple,
        'mensaje': mensaje
    })

@validacion_bp.route('/asignaturas-solicitud/<id_solicitud>', methods=['GET'])
@token_required
def validar_asignaturas_solicitud(current_user, id_solicitud):
    """Valida que las asignaturas de una solicitud cumplan con los requisitos mínimos"""
    cumple, mensaje = ValidacionService.validar_asignaturas_solicitud(id_solicitud)
    
    return jsonify({
        'cumple_requisitos': cumple,
        'mensaje': mensaje
    })

@validacion_bp.route('/proceso-aprobacion/<id_solicitud>/<nivel_aprobacion>', methods=['GET'])
@token_required
def validar_proceso_aprobacion(current_user, id_solicitud, nivel_aprobacion):
    """Valida si una solicitud puede avanzar al siguiente nivel de aprobación"""
    puede_avanzar, mensaje = ValidacionService.validar_proceso_aprobacion(id_solicitud, nivel_aprobacion)
    
    return jsonify({
        'puede_avanzar': puede_avanzar,
        'mensaje': mensaje
    })

@validacion_bp.route('/homologacion-resultados/<id_solicitud>', methods=['GET'])
@token_required
def validar_homologacion_resultados(current_user, id_solicitud):
    """Valida si los resultados de una solicitud pueden ser homologados"""
    puede_homologar, mensaje = ValidacionService.validar_homologacion_resultados(id_solicitud)
    
    return jsonify({
        'puede_homologar': puede_homologar,
        'mensaje': mensaje
    })

@validacion_bp.route('/finalizacion-intercambio/<id_solicitud>', methods=['GET'])
@token_required
def validar_finalizacion_intercambio(current_user, id_solicitud):
    """Valida si un intercambio puede ser finalizado"""
    puede_finalizar, mensaje = ValidacionService.validar_finalizacion_intercambio(id_solicitud)
    
    return jsonify({
        'puede_finalizar': puede_finalizar,
        'mensaje': mensaje
    })