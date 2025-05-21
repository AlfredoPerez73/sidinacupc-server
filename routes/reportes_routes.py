from flask import Blueprint, request, jsonify, send_file
from models.reporte import Reporte
from db.db import serialize_doc, serialize_list
from middlewares.auth import token_required
import json
import traceback
import csv
import os
import tempfile
from datetime import datetime

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/estadisticas/periodo/<periodo>', methods=['GET'])
@token_required
def estadisticas_periodo(current_user, periodo):
    """Obtiene estadísticas por periodo académico"""
    stats = Reporte.generar_estadisticas_por_periodo(periodo)
    
    return jsonify(stats)

@reportes_bp.route('/estadisticas/tipo', methods=['GET'])
@token_required
def estadisticas_tipo(current_user):
    """Obtiene estadísticas por tipo de intercambio"""
    año = request.args.get('año')
    
    stats = Reporte.generar_estadisticas_por_tipo(año)
    
    return jsonify(stats)

@reportes_bp.route('/estadisticas/facultad', methods=['GET'])
@token_required
def estadisticas_facultad(current_user):
    """Obtiene estadísticas por facultad"""
    stats = Reporte.generar_estadisticas_por_facultad()
    
    return jsonify(serialize_list(stats))

@reportes_bp.route('/estadisticas/institucion', methods=['GET'])
@token_required
def estadisticas_institucion(current_user):
    """Obtiene estadísticas por institución destino"""
    stats = Reporte.generar_estadisticas_por_institucion()
    
    return jsonify(serialize_list(stats))

@reportes_bp.route('/completo', methods=['GET'])
@token_required
def reporte_completo(current_user):
    """Genera un reporte completo con todas las estadísticas"""
    reporte, reporte_id = Reporte.generar_reporte_completo()
    
    return jsonify({
        'reporte_id': reporte_id,
        'reporte': reporte
    })

@reportes_bp.route('/exportar/csv', methods=['GET'])
@token_required
def exportar_csv(current_user):
    """Exporta estadísticas a un archivo CSV"""
    try:
        tipo_reporte = request.args.get('tipo', 'completo')
        
        if tipo_reporte == 'periodo':
            periodo = request.args.get('periodo')
            if not periodo:
                return jsonify({'message': 'Se requiere el parámetro periodo'}), 400
            
            data = Reporte.generar_estadisticas_por_periodo(periodo)
            filename = f"estadisticas_periodo_{periodo}.csv"
            
            # Crear archivo temporal
            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, 'w', newline='', encoding='utf-8') as temp:
                    writer = csv.writer(temp)
                    writer.writerow(['Período', 'Total Solicitudes', 'Pendientes', 'Aprobadas', 'Rechazadas'])
                    writer.writerow([
                        data['periodo_academico'],
                        data['total_solicitudes'],
                        data['pendientes'],
                        data['aprobadas'],
                        data['rechazadas']
                    ])
                
                # Use download_name instead of attachment_filename for newer Flask versions
                return send_file(
                    path, 
                    as_attachment=True, 
                    download_name=filename,
                    mimetype='text/csv'
                )
            
            finally:
                # Ensure the temporary file is removed even if there's an exception
                if os.path.exists(path):
                    os.remove(path)
        
        elif tipo_reporte == 'completo':
            reporte, _ = Reporte.generar_reporte_completo()
            fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reporte_completo_{fecha}.csv"
            
            # Crear archivo temporal
            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, 'w', newline='', encoding='utf-8') as temp:
                    writer = csv.writer(temp)
                    
                    # Sección 1: Estadísticas por período
                    writer.writerow(['ESTADÍSTICAS POR PERÍODO'])
                    writer.writerow(['Período', 'Total Solicitudes', 'Pendientes', 'Aprobadas', 'Rechazadas'])
                    periodo_data = reporte['estadisticas_periodo']
                    writer.writerow([
                        periodo_data['periodo_academico'],
                        periodo_data['total_solicitudes'],
                        periodo_data['pendientes'],
                        periodo_data['aprobadas'],
                        periodo_data['rechazadas']
                    ])
                    writer.writerow([])
                    
                    # Sección 2: Estadísticas por tipo
                    writer.writerow(['ESTADÍSTICAS POR TIPO'])
                    writer.writerow(['Año', 'Total', 'Nacionales', 'Internacionales'])
                    tipo_data = reporte['estadisticas_tipo']
                    writer.writerow([
                        tipo_data['año'],
                        tipo_data['total'],
                        tipo_data['nacionales'],
                        tipo_data['internacionales']
                    ])
                    writer.writerow([])
                    
                    # Sección 3: Estadísticas por facultad
                    writer.writerow(['ESTADÍSTICAS POR FACULTAD'])
                    writer.writerow(['Facultad', 'Cantidad'])
                    for facultad in reporte['estadisticas_facultad']:
                        writer.writerow([
                            facultad['_id'] if facultad['_id'] is not None else 'No especificada',
                            facultad['count']
                        ])
                    writer.writerow([])
                    
                    # Sección 4: Estadísticas por institución
                    writer.writerow(['ESTADÍSTICAS POR INSTITUCIÓN'])
                    writer.writerow(['Institución', 'País', 'Cantidad'])
                    for inst in reporte['estadisticas_institucion']:
                        writer.writerow([
                            inst['_id']['institucion'] if inst['_id']['institucion'] is not None else 'No especificada',
                            inst['_id']['pais'] if inst['_id']['pais'] is not None else 'No especificado',
                            inst['count']
                        ])
                
                # Use download_name instead of attachment_filename for newer Flask versions
                return send_file(
                    path, 
                    as_attachment=True, 
                    download_name=filename,
                    mimetype='text/csv'
                )
            
            finally:
                # Ensure the temporary file is removed even if there's an exception
                if os.path.exists(path):
                    os.remove(path)
        
        return jsonify({'message': 'Tipo de reporte no válido'}), 400
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error al exportar CSV: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'message': f'Error al generar el reporte: {str(e)}'}), 500