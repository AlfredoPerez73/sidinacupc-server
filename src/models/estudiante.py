from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Estudiante:
    @staticmethod
    def create(data):
        """Crea un nuevo estudiante en la base de datos"""
        estudiante = {
            'nombre_completo': data.get('nombre_completo'),
            'programa_academico': data.get('programa_academico'),
            'facultad': data.get('facultad'),
            'semestre': data.get('semestre'),
            'creditos_cursados': data.get('creditos_cursados'),
            'promedio_academico': data.get('promedio_academico'),
            'email': data.get('email'),
            'telefono': data.get('telefono'),
            'documento_identidad': data.get('documento_identidad'),
            'tipo_documento': data.get('tipo_documento'),
            'fecha_nacimiento': data.get('fecha_nacimiento'),
            'direccion': data.get('direccion'),
            'estado': data.get('estado', 'activo'),
            'sanciones_academicas': data.get('sanciones_academicas', False),
            'sanciones_disciplinarias': data.get('sanciones_disciplinarias', False),
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.estudiantes.insert_one(estudiante)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(estudiante_id):
        """Obtiene un estudiante por su ID"""
        return mongo.db.estudiantes.find_one({'_id': ObjectId(estudiante_id)})
    
    @staticmethod
    def get_by_documento(documento):
        """Obtiene un estudiante por su número de documento"""
        return mongo.db.estudiantes.find_one({'documento_identidad': documento})
    
    @staticmethod
    def update(estudiante_id, data):
        """Actualiza los datos de un estudiante"""
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.estudiantes.update_one(
            {'_id': ObjectId(estudiante_id)},
            {'$set': data}
        )
        
        return Estudiante.get_by_id(estudiante_id)
    
    @staticmethod
    def delete(estudiante_id):
        """Elimina un estudiante (cambio de estado a inactivo)"""
        mongo.db.estudiantes.update_one(
            {'_id': ObjectId(estudiante_id)},
            {'$set': {'estado': 'inactivo', 'fecha_actualizacion': datetime.utcnow()}}
        )
        
        return True
    
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene una lista paginada de estudiantes"""
        if filters is None:
            filters = {}
            
        skip = (page - 1) * per_page
        
        estudiantes = list(mongo.db.estudiantes.find(filters)
                           .sort('nombre_completo', 1)
                           .skip(skip)
                           .limit(per_page))
        
        total = mongo.db.estudiantes.count_documents(filters)
        
        return {
            'estudiantes': estudiantes,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def cumple_requisitos_intercambio(estudiante_id):
        """Verifica si un estudiante cumple con los requisitos para intercambio"""
        estudiante = Estudiante.get_by_id(estudiante_id)
        
        if not estudiante:
            return False, "Estudiante no encontrado"
        
        # Verificar el promedio mínimo (3.7/5.0)
        if estudiante.get('promedio_academico', 0) < 3.7:
            return False, "Promedio académico insuficiente"
        
        # Verificar que haya cursado al menos el 40% de los créditos
        # Asumiendo 160 créditos totales en la carrera (ajustar según programa)
        creditos_totales = 160
        if estudiante.get('creditos_cursados', 0) < (creditos_totales * 0.4):
            return False, "No ha cursado el mínimo de créditos requeridos"
        
        # Verificar que no tenga sanciones académicas o disciplinarias
        if estudiante.get('sanciones_academicas', False):
            return False, "Tiene sanciones académicas vigentes"
        
        if estudiante.get('sanciones_disciplinarias', False):
            return False, "Tiene sanciones disciplinarias vigentes"
        
        return True, "Cumple con todos los requisitos"