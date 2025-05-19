from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Asignatura:
    @staticmethod
    def create(data):
        """Crea una nueva equivalencia de asignatura para una solicitud de intercambio"""
        asignatura = {
            'id_solicitud': ObjectId(data.get('id_solicitud')),
            'codigo_asignatura_origen': data.get('codigo_asignatura_origen'),
            'nombre_asignatura_origen': data.get('nombre_asignatura_origen'),
            'creditos_asignatura_origen': data.get('creditos_asignatura_origen'),
            'codigo_asignatura_destino': data.get('codigo_asignatura_destino'),
            'nombre_asignatura_destino': data.get('nombre_asignatura_destino'),
            'creditos_asignatura_destino': data.get('creditos_asignatura_destino'),
            'estado_equivalencia': data.get('estado_equivalencia', 'propuesta'),
            'observaciones': data.get('observaciones', ''),
            'aprobado_por': data.get('aprobado_por', None),
            'fecha_aprobacion': data.get('fecha_aprobacion', None),
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.asignaturas.insert_one(asignatura)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(id_asignatura):
        """Obtiene una asignatura por su ID"""
        return mongo.db.asignaturas.find_one({'_id': ObjectId(id_asignatura)})
    
    @staticmethod
    def get_by_solicitud(id_solicitud):
        """Obtiene todas las asignaturas para una solicitud específica"""
        return list(mongo.db.asignaturas.find({'id_solicitud': ObjectId(id_solicitud)}))
    
    @staticmethod
    def update(id_asignatura, data):
        """Actualiza los datos de una asignatura"""
        # Convertir id_solicitud a ObjectId si está presente
        if 'id_solicitud' in data:
            data['id_solicitud'] = ObjectId(data['id_solicitud'])
        
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.asignaturas.update_one(
            {'_id': ObjectId(id_asignatura)},
            {'$set': data}
        )
        
        return Asignatura.get_by_id(id_asignatura)
    
    @staticmethod
    def delete(id_asignatura):
        """Elimina una asignatura"""
        result = mongo.db.asignaturas.delete_one({'_id': ObjectId(id_asignatura)})
        return result.deleted_count > 0
    
    @staticmethod
    def aprobar_equivalencia(id_asignatura, aprobado_por):
        """Aprueba una equivalencia de asignatura"""
        data = {
            'estado_equivalencia': 'aprobada',
            'aprobado_por': aprobado_por,
            'fecha_aprobacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        mongo.db.asignaturas.update_one(
            {'_id': ObjectId(id_asignatura)},
            {'$set': data}
        )
        
        return Asignatura.get_by_id(id_asignatura)
    
    @staticmethod
    def rechazar_equivalencia(id_asignatura, observaciones, aprobado_por):
        """Rechaza una equivalencia de asignatura"""
        data = {
            'estado_equivalencia': 'rechazada',
            'observaciones': observaciones,
            'aprobado_por': aprobado_por,
            'fecha_aprobacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        mongo.db.asignaturas.update_one(
            {'_id': ObjectId(id_asignatura)},
            {'$set': data}
        )
        
        return Asignatura.get_by_id(id_asignatura)
    
    @staticmethod
    def verificar_todas_aprobadas(id_solicitud):
        """Verifica si todas las asignaturas de una solicitud están aprobadas"""
        asignaturas = Asignatura.get_by_solicitud(id_solicitud)
        
        if not asignaturas:
            return False
        
        for asignatura in asignaturas:
            if asignatura.get('estado_equivalencia') != 'aprobada':
                return False
        
        return True
    
    @staticmethod
    def obtener_total_creditos(id_solicitud):
        """Obtiene el total de créditos de las asignaturas aprobadas para una solicitud"""
        asignaturas = Asignatura.get_by_solicitud(id_solicitud)
        
        total_creditos = 0
        for asignatura in asignaturas:
            if asignatura.get('estado_equivalencia') == 'aprobada':
                total_creditos += asignatura.get('creditos_asignatura_origen', 0)
        
        return total_creditos