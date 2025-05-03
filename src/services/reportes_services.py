from models.reporte import Reporte
from datetime import datetime
import json
import csv
import tempfile
import os

class ReporteService:
    @staticmethod
    def generar_estadisticas_por_periodo(periodo_academico):
        """Genera estadísticas por periodo académico"""
        stats = Reporte.generar_estadisticas_por_periodo(periodo_academico)
        return stats, "Estadísticas generadas exitosamente"
    
    @staticmethod
    def generar_estadisticas_por_tipo(año=None):
        """Genera estadísticas por tipo de intercambio (nacional/internacional)"""
        stats = Reporte.generar_estadisticas_por_tipo(año)
        return stats, "Estadísticas generadas exitosamente"
    
    @staticmethod
    def generar_estadisticas_por_facultad():
        """Genera estadísticas de solicitudes por facultad"""
        stats = Reporte.generar_estadisticas_por_facultad()
        return stats, "Estadísticas generadas exitosamente"
    
    @staticmethod
    def generar_estadisticas_por_institucion():
        """Genera estadísticas de solicitudes por institución destino"""
        stats = Reporte.generar_estadisticas_por_institucion()
        return stats, "Estadísticas generadas exitosamente"
    
    @staticmethod
    def generar_reporte_completo():
        """Genera un reporte completo con todas las estadísticas"""
        reporte, reporte_id = Reporte.generar_reporte_completo()
        return reporte, reporte_id
    
    @staticmethod
    def exportar_csv(tipo_reporte, params=None):
        """Exporta estadísticas a un archivo CSV"""
        if params is None:
            params = {}
        
        if tipo_reporte == 'periodo':
            periodo = params.get('periodo')
            if not periodo:
                return None, "Se requiere el parámetro periodo"
            
            data = Reporte.generar_estadisticas_por_periodo(periodo)
            filename = f"estadisticas_periodo_{periodo}.csv"
            
            # Crear archivo temporal
            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, 'w', newline='') as temp:
                    writer = csv.writer(temp)
                    writer.writerow(['Período', 'Total Solicitudes', 'Pendientes', 'Aprobadas', 'Rechazadas'])
                    writer.writerow([
                        data['periodo_academico'],
                        data['total_solicitudes'],
                        data['pendientes'],
                        data['aprobadas'],
                        data['rechazadas']
                    ])
                
                return path, filename
            
            except Exception as e:
                # Eliminar el archivo temporal en caso de error
                os.remove(path)
                return None, f"Error al generar el archivo CSV: {str(e)}"
        
        elif tipo_reporte == 'completo':
            reporte, _ = Reporte.generar_reporte_completo()
            fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reporte_completo_{fecha}.csv"
            
            # Crear archivo temporal
            fd, path = tempfile.mkstemp()
            try:
                with os.fdopen(fd, 'w', newline='') as temp:
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
                        writer.writerow([facultad['_id'], facultad['count']])
                    writer.writerow([])
                    
                    # Sección 4: Estadísticas por institución
                    writer.writerow(['ESTADÍSTICAS POR INSTITUCIÓN'])
                    writer.writerow(['Institución', 'País', 'Cantidad'])
                    for inst in reporte['estadisticas_institucion']:
                        writer.writerow([
                            inst['_id']['institucion'],
                            inst['_id']['pais'],
                            inst['count']
                        ])
                
                return path, filename
            
            except Exception as e:
                # Eliminar el archivo temporal en caso de error
                os.remove(path)
                return None, f"Error al generar el archivo CSV: {str(e)}"
        
        return None, "Tipo de reporte no válido"