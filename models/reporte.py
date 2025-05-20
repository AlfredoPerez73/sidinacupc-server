from db.db import mongo
from bson import ObjectId
from datetime import datetime
import json

class Reporte:
    @staticmethod
    def generar_estadisticas_por_periodo(periodo_academico):
        """Genera estadísticas de intercambios por periodo académico"""
        pipeline = [
            {'$match': {'periodo_academico': periodo_academico}},
            {'$group': {
                '_id': '$estado_solicitud',
                'count': {'$sum': 1}
            }}
        ]
        
        resultados = list(mongo.db.solicitudes.aggregate(pipeline))
        
        # Convertir a formato más amigable
        stats = {
            'periodo_academico': periodo_academico,
            'total_solicitudes': 0,
            'pendientes': 0,
            'aprobadas': 0,
            'rechazadas': 0
        }
        
        for result in resultados:
            estado = result['_id']
            count = result['count']
            
            stats['total_solicitudes'] += count
            
            if estado == 'pendiente':
                stats['pendientes'] = count
            elif estado == 'aprobada':
                stats['aprobadas'] = count
            elif estado == 'rechazada':
                stats['rechazadas'] = count
        
        return stats
    
    @staticmethod
    def generar_estadisticas_por_tipo(año=None):
        """Genera estadísticas por tipo de intercambio (nacional/internacional)"""
        match_stage = {}
        
        if año:
            # Filtrar por año en el periodo académico (asumiendo formato "YYYY-P")
            match_stage = {'periodo_academico': {'$regex': f'^{año}'}}
        
        pipeline = [
            {'$match': match_stage},
            {'$group': {
                '_id': '$tipo_intercambio',
                'count': {'$sum': 1}
            }}
        ]
        
        resultados = list(mongo.db.solicitudes.aggregate(pipeline))
        
        stats = {
            'año': año,
            'total': 0,
            'nacionales': 0,
            'internacionales': 0
        }
        
        for result in resultados:
            tipo = result['_id']
            count = result['count']
            
            stats['total'] += count
            
            if tipo == 'nacional':
                stats['nacionales'] = count
            elif tipo == 'internacional':
                stats['internacionales'] = count
        
        return stats
    
    @staticmethod
    def generar_estadisticas_por_facultad():
        """Genera estadísticas de solicitudes por facultad"""
        # Este es un caso más complejo que requiere un lookup para relacionar con estudiantes
        pipeline = [
            {
                '$lookup': {
                    'from': 'estudiantes',
                    'localField': 'id_estudiante',
                    'foreignField': '_id',
                    'as': 'estudiante'
                }
            },
            {'$unwind': '$estudiante'},
            {
                '$group': {
                    '_id': '$estudiante.facultad',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]
        
        return list(mongo.db.solicitudes.aggregate(pipeline))
    
    @staticmethod
    def generar_estadisticas_por_institucion():
        """Genera estadísticas de solicitudes por institución destino"""
        pipeline = [
            {
                '$lookup': {
                    'from': 'convenios',
                    'localField': 'id_convenio',
                    'foreignField': '_id',
                    'as': 'convenio'
                }
            },
            {'$unwind': '$convenio'},
            {
                '$group': {
                    '_id': {
                        'institucion': '$convenio.nombre_institucion',
                        'pais': '$convenio.pais_institucion'
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}}
        ]
        
        return list(mongo.db.solicitudes.aggregate(pipeline))
    
    @staticmethod
    def generar_reporte_completo():
        """Genera un reporte completo con todas las estadísticas"""
        # Obtener el año actual
        año_actual = datetime.now().year
        
        reporte = {
            'fecha_generacion': datetime.utcnow(),
            'estadisticas_periodo': Reporte.generar_estadisticas_por_periodo(f"{año_actual}-1"),
            'estadisticas_tipo': Reporte.generar_estadisticas_por_tipo(año_actual),
            'estadisticas_facultad': Reporte.generar_estadisticas_por_facultad(),
            'estadisticas_institucion': Reporte.generar_estadisticas_por_institucion()
        }
        
        # Guardar el reporte en la base de datos
        reporte_id = mongo.db.reportes.insert_one({
            'fecha': reporte['fecha_generacion'],
            'data': json.dumps(reporte, default=str),
            'tipo': 'completo'
        }).inserted_id
        
        return reporte, str(reporte_id)