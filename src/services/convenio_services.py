from models.convenio import Convenio
from db.db import serialize_doc, serialize_list

class ConvenioService:
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene todos los convenios con filtros y paginación"""
        result = Convenio.get_all(filters, page, per_page)
        return {
            'convenios': serialize_list(result['convenios']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }
    
    @staticmethod
    def get_by_id(convenio_id):
        """Obtiene un convenio por su ID"""
        convenio = Convenio.get_by_id(convenio_id)
        return serialize_doc(convenio)
    
    @staticmethod
    def create(data):
        """Crea un nuevo convenio"""
        convenio_id = Convenio.create(data)
        return convenio_id, "Convenio creado exitosamente"
    
    @staticmethod
    def update(convenio_id, data):
        """Actualiza los datos de un convenio"""
        # Verificar si existe el convenio
        convenio = Convenio.get_by_id(convenio_id)
        if not convenio:
            return None, "Convenio no encontrado"
        
        updated = Convenio.update(convenio_id, data)
        return serialize_doc(updated), "Convenio actualizado exitosamente"
    
    @staticmethod
    def delete(convenio_id):
        """Elimina un convenio (cambia su estado a inactivo)"""
        # Verificar si existe el convenio
        convenio = Convenio.get_by_id(convenio_id)
        if not convenio:
            return False, "Convenio no encontrado"
        
        Convenio.delete(convenio_id)
        return True, "Convenio eliminado exitosamente"
    
    @staticmethod
    def get_activos():
        """Obtiene todos los convenios activos"""
        convenios = Convenio.get_activos()
        return serialize_list(convenios)
    
    @staticmethod
    def buscar_por_institucion(nombre_institucion, page=1, per_page=10):
        """Busca convenios por nombre de institución"""
        filters = {'nombre_institucion': {'$regex': nombre_institucion, '$options': 'i'}}
        result = Convenio.get_all(filters, page, per_page)
        return {
            'convenios': serialize_list(result['convenios']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }
    
    @staticmethod
    def buscar_por_pais(pais, page=1, per_page=10):
        """Busca convenios por país"""
        filters = {'pais_institucion': pais}
        result = Convenio.get_all(filters, page, per_page)
        return {
            'convenios': serialize_list(result['convenios']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }
    
    @staticmethod
    def buscar_por_tipo(tipo_convenio, page=1, per_page=10):
        """Busca convenios por tipo (nacional/internacional)"""
        filters = {'tipo_convenio': tipo_convenio}
        result = Convenio.get_all(filters, page, per_page)
        return {
            'convenios': serialize_list(result['convenios']),
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }