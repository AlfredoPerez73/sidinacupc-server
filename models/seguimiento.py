from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Seguimiento:
    @staticmethod
    def create(data):
        """Crea un nuevo seguimiento para una solicitud de intercambio"""
        seguimiento = {
            'id_solicitud': ObjectId(data.get('id_solicitud')),
            'fecha_inicio': data.get('fecha_inicio', datetime.utcnow()),
            'fecha_fin': data.get('fecha_fin'),
            'estado_actual': data.get('estado_actual', 'en proceso'),
            'reporte_avance': data.get('reporte_avance', []),
            'documentos_soporte': data.get('documentos_soporte', []),
            'evaluaciones_recibidas': data.get('evaluaciones_recibidas', []),
            'observaciones': data.get('observaciones', ''),
            'responsable_seguimiento': data.get('responsable_seguimiento'),
            'contacto_institucion_destino': data.get('contacto_institucion_destino'),
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.seguimientos.insert_one(seguimiento)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(seguimiento_id):
        """Obtiene un seguimiento por su ID"""
        return mongo.db.seguimientos.find_one({'_id': ObjectId(seguimiento_id)})
    
    @staticmethod
    def get_by_solicitud(id_solicitud):
        """Obtiene el seguimiento para una solicitud específica"""
        return mongo.db.seguimientos.find_one({'id_solicitud': ObjectId(id_solicitud)})
    
    @staticmethod
    def update(seguimiento_id, data):
        """Actualiza los datos de un seguimiento"""
        # Convertir id_solicitud a ObjectId si está presente
        if 'id_solicitud' in data:
            data['id_solicitud'] = ObjectId(data['id_solicitud'])
        
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.seguimientos.update_one(
            {'_id': ObjectId(seguimiento_id)},
            {'$set': data}
        )
        
        return Seguimiento.get_by_id(seguimiento_id)
    
    @staticmethod
    def agregar_reporte(seguimiento_id, reporte):
        """Agrega un nuevo reporte de avance al seguimiento"""
        reporte['fecha'] = datetime.utcnow()
        
        mongo.db.seguimientos.update_one(
            {'_id': ObjectId(seguimiento_id)},
            {
                '$push': {'reporte_avance': reporte},
                '$set': {'fecha_actualizacion': datetime.utcnow()}
            }
        )
        
        return Seguimiento.get_by_id(seguimiento_id)
    
    @staticmethod
    def agregar_documento(seguimiento_id, documento):
        """Agrega un nuevo documento soporte al seguimiento"""
        documento['fecha_subida'] = datetime.utcnow()
        
        mongo.db.seguimientos.update_one(
            {'_id': ObjectId(seguimiento_id)},
            {
                '$push': {'documentos_soporte': documento},
                '$set': {'fecha_actualizacion': datetime.utcnow()}
            }
        )
        
        return Seguimiento.get_by_id(seguimiento_id)
    
    @staticmethod
    def agregar_evaluacion(seguimiento_id, evaluacion):
        """Agrega una nueva evaluación al seguimiento"""
        evaluacion['fecha'] = datetime.utcnow()
        
        mongo.db.seguimientos.update_one(
            {'_id': ObjectId(seguimiento_id)},
            {
                '$push': {'evaluaciones_recibidas': evaluacion},
                '$set': {'fecha_actualizacion': datetime.utcnow()}
            }
        )
        
        return Seguimiento.get_by_id(seguimiento_id)
    
    @staticmethod
    def cambiar_estado(seguimiento_id, nuevo_estado, observaciones=None):
        """Cambia el estado actual del seguimiento"""
        update_data = {
            'estado_actual': nuevo_estado,
            'fecha_actualizacion': datetime.utcnow()
        }
        
        if nuevo_estado == 'finalizado':
            update_data['fecha_fin'] = datetime.utcnow()
        
        if observaciones:
            update_data['observaciones'] = observaciones
        
        mongo.db.seguimientos.update_one(
            {'_id': ObjectId(seguimiento_id)},
            {'$set': update_data}
        )
        
        return Seguimiento.get_by_id(seguimiento_id)
    
    @staticmethod
    def get_all_active():
        """Obtiene todos los seguimientos activos (en proceso)"""
        return list(mongo.db.seguimientos.find({'estado_actual': 'en proceso'}))
    
    @staticmethod
    def get_by_filters(filters=None, page=1, per_page=10):
        """Obtiene seguimientos con filtros y paginación"""
        if filters is None:
            filters = {}
            
        skip = (page - 1) * per_page
        
        seguimientos = list(mongo.db.seguimientos.find(filters)
                           .sort('fecha_actualizacion', -1)
                           .skip(skip)
                           .limit(per_page))
        
        total = mongo.db.seguimientos.count_documents(filters)
        
        return {
            'seguimientos': seguimientos,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }