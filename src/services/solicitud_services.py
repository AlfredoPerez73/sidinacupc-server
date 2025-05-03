from models.solicitud import Solicitud
from models.estudiante import Estudiante
from models.convenio import Convenio
from models.asignatura import Asignatura
from models.seguimiento import Seguimiento
from db.db import serialize_doc, serialize_list
from bson import ObjectId

class SolicitudService:
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene todas las solicitudes con filtros y paginación"""
        result = Solicitud.get_all(filters, page, per_page)
        
        # Enriquecer las solicitudes con datos de estudiantes y convenios
        solicitudes_enriquecidas = []
        for solicitud in result['solicitudes']:
            solicitud_dict = serialize_doc(solicitud)
            
            # Agregar información del estudiante
            estudiante = Estudiante.get_by_id(str(solicitud['estudiante_id']))
            if estudiante:
                solicitud_dict['estudiante'] = {
                    'nombre': estudiante.get('nombre_completo'),
                    'programa': estudiante.get('programa_academico'),
                    'facultad': estudiante.get('facultad')
                }
            
            # Agregar información del convenio
            convenio = Convenio.get_by_id(str(solicitud['convenio_id']))
            if convenio:
                solicitud_dict['convenio'] = {
                    'nombre_institucion': convenio.get('nombre_institucion'),
                    'pais': convenio.get('pais_institucion'),
                    'tipo': convenio.get('tipo_convenio')
                }
            
            solicitudes_enriquecidas.append(solicitud_dict)
        
        return {
            'solicitudes': solicitudes_enriquecidas,
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages']
        }
    
    @staticmethod
    def get_by_id(solicitud_id):
        """Obtiene una solicitud por su ID con datos enriquecidos"""
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        solicitud_dict = serialize_doc(solicitud)
        
        # Agregar información del estudiante
        estudiante = Estudiante.get_by_id(str(solicitud['estudiante_id']))
        if estudiante:
            solicitud_dict['estudiante'] = serialize_doc(estudiante)
        
        # Agregar información del convenio
        convenio = Convenio.get_by_id(str(solicitud['convenio_id']))
        if convenio:
            solicitud_dict['convenio'] = serialize_doc(convenio)
        
        # Agregar información de asignaturas
        asignaturas = Asignatura.get_by_solicitud(solicitud_id)
        if asignaturas:
            solicitud_dict['asignaturas'] = serialize_list(asignaturas)
        
        # Agregar información de seguimiento
        seguimiento = Seguimiento.get_by_solicitud(solicitud_id)
        if seguimiento:
            solicitud_dict['seguimiento'] = serialize_doc(seguimiento)
        
        return solicitud_dict, "Solicitud encontrada exitosamente"
    
    @staticmethod
    def get_by_estudiante(estudiante_id, page=1, per_page=10):
        """Obtiene todas las solicitudes de un estudiante"""
        filters = {'estudiante_id': ObjectId(estudiante_id)}
        return SolicitudService.get_all(filters, page, per_page)
    
    @staticmethod
    def create(data):
        """Crea una nueva solicitud de intercambio"""
        # Verificar que el estudiante exista
        estudiante = Estudiante.get_by_id(data['estudiante_id'])
        if not estudiante:
            return None, "Estudiante no encontrado"
        
        # Verificar que el convenio exista
        convenio = Convenio.get_by_id(data['convenio_id'])
        if not convenio:
            return None, "Convenio no encontrado"
        
        # Verificar que el estudiante cumpla con los requisitos
        cumple, mensaje = Estudiante.cumple_requisitos_intercambio(data['estudiante_id'])
        if not cumple:
            return None, f"El estudiante no cumple con los requisitos: {mensaje}"
        
        # Crear la solicitud
        solicitud_id = Solicitud.create(data)
        
        # Si se han incluido asignaturas en la solicitud, crearlas
        if 'asignaturas' in data and isinstance(data['asignaturas'], list):
            for asignatura_data in data['asignaturas']:
                asignatura_data['solicitud_id'] = solicitud_id
                Asignatura.create(asignatura_data)
        
        # Crear un seguimiento inicial para la solicitud
        seguimiento_data = {
            'solicitud_id': solicitud_id,
            'estado_actual': 'pendiente',
            'observaciones': 'Solicitud creada'
        }
        Seguimiento.create(seguimiento_data)
        
        return solicitud_id, "Solicitud creada exitosamente"
    
    @staticmethod
    def update(solicitud_id, data):
        """Actualiza los datos de una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Si se está actualizando el estudiante, verificar que exista
        if 'estudiante_id' in data:
            estudiante = Estudiante.get_by_id(data['estudiante_id'])
            if not estudiante:
                return None, "Estudiante no encontrado"
        
        # Si se está actualizando el convenio, verificar que exista
        if 'convenio_id' in data:
            convenio = Convenio.get_by_id(data['convenio_id'])
            if not convenio:
                return None, "Convenio no encontrado"
        
        updated = Solicitud.update(solicitud_id, data)
        return serialize_doc(updated), "Solicitud actualizada exitosamente"
    
    @staticmethod
    def update_estado(solicitud_id, nuevo_estado, comentarios=None):
        """Actualiza el estado de una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Validar estado
        estados_validos = ['pendiente', 'en revision', 'aprobada', 'rechazada', 'finalizada']
        if nuevo_estado not in estados_validos:
            return None, f"Estado no válido. Estados permitidos: {', '.join(estados_validos)}"
        
        updated = Solicitud.update_estado(solicitud_id, nuevo_estado, comentarios)
        
        # Actualizar también el estado del seguimiento
        seguimiento = Seguimiento.get_by_solicitud(solicitud_id)
        if seguimiento:
            estado_seguimiento = 'en proceso' if nuevo_estado == 'aprobada' else nuevo_estado
            Seguimiento.cambiar_estado(str(seguimiento['_id']), estado_seguimiento, comentarios)
        
        return serialize_doc(updated), f"Estado de solicitud actualizado a {nuevo_estado}"
    
    @staticmethod
    def proceso_aprobacion(solicitud_id, nivel_aprobacion, aprobado=True, comentarios=None):
        """Gestiona el proceso de aprobación multinivel de las solicitudes"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        if nivel_aprobacion == 'jefe_programa':
            if aprobado:
                updated = Solicitud.aprobar_jefe_programa(solicitud_id)
                mensaje = "Solicitud aprobada por el jefe de programa"
            else:
                updated = Solicitud.update_estado(solicitud_id, 'rechazada', comentarios)
                mensaje = "Solicitud rechazada por el jefe de programa"
                
        elif nivel_aprobacion == 'consejo_facultad':
            # Solo se puede aprobar si ya fue aprobada por el jefe de programa
            if not solicitud.get('jefe_programa_aprobacion'):
                return None, "La solicitud debe ser aprobada primero por el jefe de programa"
                
            if aprobado:
                updated = Solicitud.aprobar_consejo_facultad(solicitud_id)
                mensaje = "Solicitud aprobada por el consejo de facultad"
            else:
                updated = Solicitud.update_estado(solicitud_id, 'rechazada', comentarios)
                mensaje = "Solicitud rechazada por el consejo de facultad"
                
        elif nivel_aprobacion == 'orpi':
            # Solo se puede aprobar si ya fue aprobada por el consejo de facultad
            if not solicitud.get('consejo_facultad_aprobacion'):
                return None, "La solicitud debe ser aprobada primero por el consejo de facultad"
                
            if aprobado:
                updated, msg = Solicitud.aprobar_ORPI(solicitud_id)
                if not updated:
                    return None, msg
                mensaje = "Solicitud aprobada por la oficina de ORPI"
                
                # Cambiar el estado del seguimiento a 'en proceso'
                seguimiento = Seguimiento.get_by_solicitud(solicitud_id)
                if seguimiento:
                    Seguimiento.cambiar_estado(str(seguimiento['_id']), 'en proceso', 
                                              "Intercambio aprobado y en proceso")
            else:
                updated = Solicitud.update_estado(solicitud_id, 'rechazada', comentarios)
                mensaje = "Solicitud rechazada por la oficina de ORPI"
        else:
            return None, "Nivel de aprobación no válido"
        
        return serialize_doc(updated), mensaje
    
    @staticmethod
    def agregar_documento(solicitud_id, documento):
        """Agrega un documento a la solicitud"""
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        updated = Solicitud.agregar_documento(solicitud_id, documento)
        return serialize_doc(updated), "Documento agregado exitosamente"
    
    @staticmethod
    def buscar_por_periodo(periodo_academico, page=1, per_page=10):
        """Busca solicitudes por periodo académico"""
        filters = {'periodo_academico': periodo_academico}
        return SolicitudService.get_all(filters, page, per_page)
    
    @staticmethod
    def buscar_por_estado(estado, page=1, per_page=10):
        """Busca solicitudes por estado"""
        filters = {'estado_solicitud': estado}
        return SolicitudService.get_all(filters, page, per_page)
    
    @staticmethod
    def buscar_por_tipo_intercambio(tipo, page=1, per_page=10):
        """Busca solicitudes por tipo de intercambio"""
        filters = {'tipo_intercambio': tipo}
        return SolicitudService.get_all(filters, page, per_page)