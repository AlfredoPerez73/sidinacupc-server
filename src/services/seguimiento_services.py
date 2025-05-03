from models.seguimiento import Seguimiento
from models.solicitud import Solicitud
from db.db import serialize_doc, serialize_list
from bson import ObjectId

class SeguimientoService:
    @staticmethod
    def get_by_id(seguimiento_id):
        """Obtiene un seguimiento por su ID"""
        seguimiento = Seguimiento.get_by_id(seguimiento_id)
        return serialize_doc(seguimiento)
    
    @staticmethod
    def get_by_solicitud(solicitud_id):
        """Obtiene el seguimiento para una solicitud específica"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        seguimiento = Seguimiento.get_by_solicitud(solicitud_id)
        return serialize_doc(seguimiento), "Seguimiento encontrado exitosamente"
    
    @staticmethod
    def create(data):
        """Crea un nuevo seguimiento para una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(data['solicitud_id'])
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Verificar si ya existe un seguimiento para esta solicitud
        existing = Seguimiento.get_by_solicitud(data['solicitud_id'])
        if existing:
            return None, "Ya existe un seguimiento para esta solicitud"
        
        seguimiento_id = Seguimiento.create(data)
        return seguimiento_id, "Seguimiento creado exitosamente"
    
    @staticmethod
    def update(seguimiento_id, data):
        """Actualiza los datos de un seguimiento"""
        # Verificar si existe el seguimiento
        seguimiento = Seguimiento.get_by_id(seguimiento_id)
        if not seguimiento:
            return None, "Seguimiento no encontrado"
        
        # Si se está cambiando la solicitud, verificar que exista
        if 'solicitud_id' in data:
            solicitud = Solicitud.get_by_id(data['solicitud_id'])
            if not solicitud:
                return None, "Solicitud no encontrada"
            
            # Verificar que no exista otro seguimiento para la nueva solicitud
            existing = Seguimiento.get_by_solicitud(data['solicitud_id'])
            if existing and str(existing['_id']) != seguimiento_id:
                return None, "Ya existe un seguimiento para esta solicitud"
        
        updated = Seguimiento.update(seguimiento_id, data)
        return serialize_doc(updated), "Seguimiento actualizado exitosamente"
    
    @staticmethod
    def agregar_reporte(seguimiento_id, reporte):
        """Agrega un nuevo reporte de avance al seguimiento"""
        # Verificar si existe el seguimiento
        seguimiento = Seguimiento.get_by_id(seguimiento_id)
        if not seguimiento:
            return None, "Seguimiento no encontrado"
        
        # Validar campos requeridos
        if 'contenido' not in reporte or not reporte['contenido']:
            return None, "El contenido del reporte es requerido"
        
        updated = Seguimiento.agregar_reporte(seguimiento_id, reporte)
        return serialize_doc(updated), "Reporte agregado exitosamente"
    
    @staticmethod
    def agregar_documento(seguimiento_id, documento):
        """Agrega un nuevo documento soporte al seguimiento"""
        # Verificar si existe el seguimiento
        seguimiento = Seguimiento.get_by_id(seguimiento_id)
        if not seguimiento:
            return None, "Seguimiento no encontrado"
        
        # Validar campos requeridos
        if 'nombre' not in documento or not documento['nombre']:
            return None, "El nombre del documento es requerido"
        
        if 'archivo' not in documento or not documento['archivo']:
            return None, "El archivo es requerido"
        
        updated = Seguimiento.agregar_documento(seguimiento_id, documento)
        return serialize_doc(updated), "Documento agregado exitosamente"
    
    @staticmethod
    def agregar_evaluacion(seguimiento_id, evaluacion):
        """Agrega una nueva evaluación al seguimiento"""
        # Verificar si existe el seguimiento
        seguimiento = Seguimiento.get_by_id(seguimiento_id)
        if not seguimiento:
            return None, "Seguimiento no encontrado"
        
        # Validar campos requeridos
        if 'calificacion' not in evaluacion or evaluacion['calificacion'] is None:
            return None, "La calificación es requerida"
        
        if 'comentarios' not in evaluacion or not evaluacion['comentarios']:
            return None, "Los comentarios son requeridos"
        
        updated = Seguimiento.agregar_evaluacion(seguimiento_id, evaluacion)
        return serialize_doc(updated), "Evaluación agregada exitosamente"
    
    @staticmethod
    def cambiar_estado(seguimiento_id, nuevo_estado, observaciones=None):
        """Cambia el estado actual del seguimiento"""
        # Verificar si existe el seguimiento
        seguimiento = Seguimiento.get_by_id(seguimiento_id)
        if not seguimiento:
            return None, "Seguimiento no encontrado"
        
        # Validar estado
        estados_validos = ['pendiente', 'en proceso', 'finalizado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return None, f"Estado no válido. Estados permitidos: {', '.join(estados_validos)}"
        
        updated = Seguimiento.cambiar_estado(seguimiento_id, nuevo_estado, observaciones)
        
        # Si el estado cambia a 'finalizado', actualizar también la solicitud
        if nuevo_estado == 'finalizado':
            solicitud_id = str(seguimiento['solicitud_id'])
            Solicitud.update_estado(solicitud_id, 'finalizada', observaciones)
        
        return serialize_doc(updated), f"Estado del seguimiento actualizado a {nuevo_estado}"
    
    @staticmethod
    def get_all_active():
        """Obtiene todos los seguimientos activos (en proceso)"""
        seguimientos = Seguimiento.get_all_active()
        
        # Enriquecer los datos con información de la solicitud
        seguimientos_enriquecidos = []
        for seguimiento in seguimientos:
            seguimiento_dict = serialize_doc(seguimiento)
            
            # Agregar información de la solicitud
            solicitud = Solicitud.get_by_id(str(seguimiento['solicitud_id']))
            if solicitud:
                estudiante = estudiante.get_by_id(str(solicitud['estudiante_id']))
                convenio = convenio.get_by_id(str(solicitud['convenio_id']))
                
                seguimiento_dict['solicitud'] = {
                    'id': str(solicitud['_id']),
                    'periodo_academico': solicitud.get('periodo_academico'),
                    'tipo_intercambio': solicitud.get('tipo_intercambio'),
                    'estudiante': estudiante.get('nombre_completo') if estudiante else None,
                    'institucion': convenio.get('nombre_institucion') if convenio else None
                }
            
            seguimientos_enriquecidos.append(seguimiento_dict)
        
        return seguimientos_enriquecidos
    
    @staticmethod
    def get_by_filters(filters=None, page=1, per_page=10):
        """Obtiene seguimientos con filtros y paginación"""
        result = Seguimiento.get_by_filters(filters, page, per_page)
        
        # Enriquecer los datos con información de la solicitud
        seguimientos_enriquecidos = []
        for seguimiento in result['seguimientos']:
            seguimiento_dict = serialize_doc(seguimiento)
            
            # Agregar información de la solicitud
            solicitud = Solicitud.get_by_id(str(seguimiento['solicitud_id']))
            if solicitud:
                estudiante = estudiante.get_by_id(str(solicitud['estudiante_id']))
                convenio = convenio.get_by_id(str(solicitud['convenio_id']))
                
                seguimiento_dict['solicitud'] = {
                    'id': str(solicitud['_id']),
                    'periodo_academico': solicitud.get('periodo_academico'),
                    'tipo_intercambio': solicitud.get('tipo_intercambio'),
                    'estudiante': estudiante.get('nombre_completo') if estudiante else None,
                    'institucion': convenio.get('nombre_institucion') if convenio else None
                }
            
            seguimientos_enriquecidos.append(seguimiento_dict)
        
        return {
            'seguimientos': seguimientos_enriquecidos,
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }