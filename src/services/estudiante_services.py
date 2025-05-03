from models.estudiante import Estudiante
from bson import ObjectId
from db.db import serialize_doc, serialize_list

class EstudianteService:
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene todos los estudiantes con filtros y paginación"""
        result = Estudiante.get_all(filters, page, per_page)
        return {
            'estudiantes': serialize_list(result['estudiantes']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }
    
    @staticmethod
    def get_by_id(estudiante_id):
        """Obtiene un estudiante por su ID"""
        estudiante = Estudiante.get_by_id(estudiante_id)
        return serialize_doc(estudiante)
    
    @staticmethod
    def get_by_documento(documento):
        """Obtiene un estudiante por su documento de identidad"""
        estudiante = Estudiante.get_by_documento(documento)
        return serialize_doc(estudiante)
    
    @staticmethod
    def create(data):
        """Crea un nuevo estudiante"""
        # Verificar si ya existe un estudiante con el mismo documento
        existing = Estudiante.get_by_documento(data['documento_identidad'])
        if existing:
            return None, "Ya existe un estudiante con este documento de identidad"
        
        estudiante_id = Estudiante.create(data)
        return estudiante_id, "Estudiante creado exitosamente"
    
    @staticmethod
    def update(estudiante_id, data):
        """Actualiza los datos de un estudiante"""
        # Verificar si existe el estudiante
        estudiante = Estudiante.get_by_id(estudiante_id)
        if not estudiante:
            return None, "Estudiante no encontrado"
        
        # Si se está actualizando el documento, verificar que no exista otro con ese documento
        if 'documento_identidad' in data:
            existing = Estudiante.get_by_documento(data['documento_identidad'])
            if existing and str(existing['_id']) != estudiante_id:
                return None, "Ya existe otro estudiante con este documento de identidad"
        
        updated = Estudiante.update(estudiante_id, data)
        return serialize_doc(updated), "Estudiante actualizado exitosamente"
    
    @staticmethod
    def delete(estudiante_id):
        """Elimina un estudiante (cambia su estado a inactivo)"""
        # Verificar si existe el estudiante
        estudiante = Estudiante.get_by_id(estudiante_id)
        if not estudiante:
            return False, "Estudiante no encontrado"
        
        Estudiante.delete(estudiante_id)
        return True, "Estudiante eliminado exitosamente"
    
    @staticmethod
    def verificar_requisitos(estudiante_id):
        """Verifica si un estudiante cumple con los requisitos para intercambio"""
        # Verificar si existe el estudiante
        estudiante = Estudiante.get_by_id(estudiante_id)
        if not estudiante:
            return False, "Estudiante no encontrado"
        
        cumple, mensaje = Estudiante.cumple_requisitos_intercambio(estudiante_id)
        return cumple, mensaje
    
    @staticmethod
    def buscar_por_nombre(nombre, page=1, per_page=10):
        """Busca estudiantes por nombre"""
        filters = {'nombre_completo': {'$regex': nombre, '$options': 'i'}}
        result = Estudiante.get_all(filters, page, per_page)
        return {
            'estudiantes': serialize_list(result['estudiantes']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }
    
    @staticmethod
    def buscar_por_programa(programa, page=1, per_page=10):
        """Busca estudiantes por programa académico"""
        filters = {'programa_academico': programa}
        result = Estudiante.get_all(filters, page, per_page)
        return {
            'estudiantes': serialize_list(result['estudiantes']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }