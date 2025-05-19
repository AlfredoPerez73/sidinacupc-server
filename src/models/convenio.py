from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Convenio:
    @staticmethod
    def create(data):
        """Crea un nuevo convenio en la base de datos"""
        convenio = {
            'nombre_institucion': data.get('nombre_institucion'),
            'pais_institucion': data.get('pais_institucion'),
            'ciudad_institucion': data.get('ciudad_institucion'),
            'tipo_convenio': data.get('tipo_convenio'),
            'fecha_inicio': data.get('fecha_inicio'),
            'fecha_fin': data.get('fecha_fin'),
            'estado': data.get('estado', 'activo'),
            'descripcion': data.get('descripcion'),
            'documentacion_url': data.get('documentacion_url'),
            'requisitos_especificos': data.get('requisitos_especificos'),
            'beneficios': data.get('beneficios'),
            'cupos_disponibles': data.get('cupos_disponibles'),
            'contacto_institucion': data.get('contacto_institucion'),
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.convenios.insert_one(convenio)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(id_convenio):
        """Obtiene un convenio por su ID"""
        return mongo.db.convenios.find_one({'_id': ObjectId(id_convenio)})
    
    @staticmethod
    def update(id_convenio, data):
        """Actualiza los datos de un convenio"""
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.convenios.update_one(
            {'_id': ObjectId(id_convenio)},
            {'$set': data}
        )
        
        return Convenio.get_by_id(id_convenio)
    
    @staticmethod
    def delete(id_convenio):
        """Elimina un convenio (cambio de estado a inactivo)"""
        mongo.db.convenios.update_one(
            {'_id': ObjectId(id_convenio)},
            {'$set': {'estado': 'inactivo', 'fecha_actualizacion': datetime.utcnow()}}
        )
        
        return True
    
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene una lista paginada de convenios"""
        if filters is None:
            filters = {}
            
        skip = (page - 1) * per_page
        
        convenios = list(mongo.db.convenios.find(filters)
                         .sort('nombre_institucion', 1)
                         .skip(skip)
                         .limit(per_page))
        
        total = mongo.db.convenios.count_documents(filters)
        
        return {
            'convenios': convenios,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def get_activos():
        """Obtiene todos los convenios activos"""
        now = datetime.utcnow()
        return list(mongo.db.convenios.find({
            'estado': 'activo',
            'fecha_fin': {'$gt': now}
        }).sort('nombre_institucion', 1))