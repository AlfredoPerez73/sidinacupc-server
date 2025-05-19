from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Solicitud:
    @staticmethod
    def create(data):
        """Crea una nueva solicitud de intercambio en la base de datos"""
        solicitud = {
            'id_solicitante': ObjectId(data.get('id_solicitante')),
            'id_convenio': ObjectId(data.get('id_convenio')),
            'fecha_solicitud': datetime.utcnow(),
            'estado_solicitud': 'pendiente',
            'periodo_academico': data.get('periodo_academico'),
            'modalidad': data.get('modalidad'),
            'tipo_intercambio': data.get('tipo_intercambio'),
            'duracion': data.get('duracion'),
            'tipo_solicitante': data.get('tipo_solicitante', 'estudiante'),  # Nuevo campo para identificar si es estudiante o docente
            'documentos_adjuntos': data.get('documentos_adjuntos', []),
            'fecha_decision': None,
            'comentarios_decision': None,
            'jefe_programa_aprobacion': False,
            'consejo_facultad_aprobacion': False,
            'oficina_ORPI_aprobacion': False,
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.solicitudes.insert_one(solicitud)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(solicitud_id):
        """Obtiene una solicitud por su ID"""
        return mongo.db.solicitudes.find_one({'_id': ObjectId(solicitud_id)})
    
    @staticmethod
    def get_by_solicitante(id_solicitante):
        """Obtiene todas las solicitudes de un solicitante (estudiante o docente)"""
        return list(mongo.db.solicitudes.find({'id_solicitante': ObjectId(id_solicitante)}))
    
    @staticmethod
    def update(solicitud_id, data):
        """Actualiza los datos de una solicitud"""
        # Convertir IDs a ObjectId si están presentes
        if 'id_solicitante' in data:
            data['id_solicitante'] = ObjectId(data['id_solicitante'])
        if 'id_convenio' in data:
            data['id_convenio'] = ObjectId(data['id_convenio'])
        
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.solicitudes.update_one(
            {'_id': ObjectId(solicitud_id)},
            {'$set': data}
        )
        
        return Solicitud.get_by_id(solicitud_id)
    
    @staticmethod
    def update_estado(solicitud_id, nuevo_estado, comentarios=None):
        """Actualiza el estado de una solicitud"""
        update_data = {
            'estado_solicitud': nuevo_estado,
            'fecha_actualizacion': datetime.utcnow()
        }
        
        if nuevo_estado in ['aprobada', 'rechazada']:
            update_data['fecha_decision'] = datetime.utcnow()
            
        if comentarios:
            update_data['comentarios_decision'] = comentarios
        
        mongo.db.solicitudes.update_one(
            {'_id': ObjectId(solicitud_id)},
            {'$set': update_data}
        )
        
        return Solicitud.get_by_id(solicitud_id)
    
    @staticmethod
    def aprobar_jefe_programa(solicitud_id):
        """Marca una solicitud como aprobada por el jefe de programa"""
        mongo.db.solicitudes.update_one(
            {'_id': ObjectId(solicitud_id)},
            {'$set': {
                'jefe_programa_aprobacion': True,
                'fecha_actualizacion': datetime.utcnow()
            }}
        )
        
        return Solicitud.get_by_id(solicitud_id)
    
    @staticmethod
    def aprobar_consejo_facultad(solicitud_id):
        """Marca una solicitud como aprobada por el consejo de facultad"""
        mongo.db.solicitudes.update_one(
            {'_id': ObjectId(solicitud_id)},
            {'$set': {
                'consejo_facultad_aprobacion': True,
                'fecha_actualizacion': datetime.utcnow()
            }}
        )
        
        return Solicitud.get_by_id(solicitud_id)
    
    @staticmethod
    def aprobar_ORPI(solicitud_id):
        """Marca una solicitud como aprobada por la oficina de ORPI"""
        solicitud = Solicitud.get_by_id(solicitud_id)
        
        # Verificar que ya tenga las aprobaciones previas
        if not solicitud.get('jefe_programa_aprobacion') or not solicitud.get('consejo_facultad_aprobacion'):
            return None, "La solicitud no tiene las aprobaciones previas requeridas"
        
        mongo.db.solicitudes.update_one(
            {'_id': ObjectId(solicitud_id)},
            {'$set': {
                'oficina_ORPI_aprobacion': True,
                'estado_solicitud': 'aprobada',
                'fecha_decision': datetime.utcnow(),
                'fecha_actualizacion': datetime.utcnow()
            }}
        )
        
        return Solicitud.get_by_id(solicitud_id), "Solicitud aprobada exitosamente"
    
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene una lista paginada de solicitudes"""
        if filters is None:
            filters = {}
            
        skip = (page - 1) * per_page
        
        solicitudes = list(mongo.db.solicitudes.find(filters)
                           .sort('fecha_solicitud', -1)
                           .skip(skip)
                           .limit(per_page))
        
        total = mongo.db.solicitudes.count_documents(filters)
        
        return {
            'solicitudes': solicitudes,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def agregar_documento(solicitud_id, documento):
        """Agrega un documento a la solicitud"""
        mongo.db.solicitudes.update_one(
            {'_id': ObjectId(solicitud_id)},
            {'$push': {'documentos_adjuntos': documento}}
        )
        
        return Solicitud.get_by_id(solicitud_id)