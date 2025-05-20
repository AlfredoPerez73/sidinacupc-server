import pandas as pd
from models.solicitud import Solicitud
from models.estudiante import Estudiante
from models.docente import Docente
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
        
        # Enriquecer las solicitudes con datos de solicitantes y convenios
        solicitudes_enriquecidas = []
        for solicitud in result['solicitudes']:
            solicitud_dict = serialize_doc(solicitud)
            
            # Agregar información del solicitante (puede ser estudiante o docente)
            id_solicitante = str(solicitud['id_solicitante'])
            tipo_solicitante = solicitud.get('tipo_solicitante', 'estudiante')
            
            if tipo_solicitante == 'estudiante':
                solicitante = Estudiante.get_by_id(id_solicitante)
                if solicitante:
                    solicitud_dict['solicitante'] = {
                        'nombre': solicitante.get('nombre_completo'),
                        'programa': solicitante.get('programa_academico'),
                        'facultad': solicitante.get('facultad'),
                        'tipo': 'estudiante'
                    }
            else:  # docente
                solicitante = Docente.get_by_id(id_solicitante)
                if solicitante:
                    solicitud_dict['solicitante'] = {
                        'nombre': solicitante.get('nombre_completo'),
                        'departamento': solicitante.get('departamento'),
                        'facultad': solicitante.get('facultad'),
                        'tipo': 'docente'
                    }
            
            # Agregar información del convenio
            convenio = Convenio.get_by_id(str(solicitud['id_convenio']))
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
    def importar_csv(archivo_csv):
        try:
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar estructura del CSV
            campos_requeridos = [
                'id_solicitante', 'tipo_solicitante', 'id_convenio', 'periodo_academico',
                'modalidad', 'tipo_intercambio', 'duracion'
            ]
            for campo in campos_requeridos:
                if campo not in df.columns:
                    return None, f"El campo {campo} es requerido en el CSV"
            
            # Procesar cada registro
            resultados = []
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Verificar si existe el solicitante según su tipo
                    id_solicitante = row['id_solicitante']
                    tipo_solicitante = row.get('tipo_solicitante', 'estudiante')
                    
                    if tipo_solicitante == 'estudiante':
                        solicitante = Estudiante.get_by_id(id_solicitante)
                        
                        if not solicitante:
                            # Verificar si es un documento en lugar de ID
                            if id_solicitante.isdigit() or (isinstance(id_solicitante, str) and len(id_solicitante) < 15):
                                solicitante = Estudiante.get_by_documento(str(id_solicitante))
                                if solicitante:
                                    id_solicitante = str(solicitante['_id'])
                        
                        if not solicitante:
                            raise ValueError(f"Estudiante no encontrado: {id_solicitante}")
                        
                        # Verificar requisitos del estudiante
                        cumple, mensaje = Estudiante.cumple_requisitos_intercambio(id_solicitante)
                        if not cumple:
                            raise ValueError(f"El estudiante no cumple requisitos: {mensaje}")
                    else:  # docente
                        solicitante = Docente.get_by_id(id_solicitante)
                        
                        if not solicitante:
                            # Verificar si es un documento en lugar de ID
                            if id_solicitante.isdigit() or (isinstance(id_solicitante, str) and len(id_solicitante) < 15):
                                solicitante = Docente.get_by_documento(str(id_solicitante))
                                if solicitante:
                                    id_solicitante = str(solicitante['_id'])
                        
                        if not solicitante:
                            raise ValueError(f"Docente no encontrado: {id_solicitante}")
                        
                        # Verificar requisitos del docente si existen
                        if hasattr(Docente, 'cumple_requisitos_intercambio'):
                            cumple, mensaje = Docente.cumple_requisitos_intercambio(id_solicitante)
                            if not cumple:
                                raise ValueError(f"El docente no cumple requisitos: {mensaje}")
                    
                    # Verificar si existe el convenio
                    id_convenio = row['id_convenio']
                    convenio = Convenio.get_by_id(id_convenio)
                    
                    if not convenio:
                        raise ValueError(f"Convenio no encontrado: {id_convenio}")
                    
                    # Crear solicitud
                    solicitud_data = {
                        'id_solicitante': id_solicitante,
                        'tipo_solicitante': tipo_solicitante,
                        'id_convenio': id_convenio,
                        'periodo_academico': row['periodo_academico'],
                        'modalidad': row['modalidad'],
                        'tipo_intercambio': row['tipo_intercambio'],
                        'duracion': int(row['duracion']),
                        'estado_solicitud': 'pendiente'
                    }
                    
                    # Insertar en la base de datos
                    id_solicitud = Solicitud.create(solicitud_data)
                    resultados.append(id_solicitud)
                    
                except Exception as e:
                    # Registrar error para este registro
                    errores.append({
                        'fila': index + 2,
                        'error': str(e),
                        'datos': row.to_dict()
                    })
            
            return {
                'total_importados': len(resultados),
                'solicitudes_creadas': resultados,
                'errores': errores
            }, "Solicitudes importadas con éxito"
        
        except Exception as e:
            return None, f"Error al procesar el archivo CSV: {str(e)}"
    
    @staticmethod
    def get_by_id(id_solicitud):
        """Obtiene una solicitud por su ID con datos enriquecidos"""
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        solicitud_dict = serialize_doc(solicitud)
        
        # Agregar información del solicitante según su tipo
        id_solicitante = str(solicitud['id_solicitante'])
        tipo_solicitante = solicitud.get('tipo_solicitante', 'estudiante')
        
        if tipo_solicitante == 'estudiante':
            solicitante = Estudiante.get_by_id(id_solicitante)
            if solicitante:
                solicitud_dict['solicitante'] = serialize_doc(solicitante)
                solicitud_dict['solicitante']['tipo'] = 'estudiante'
        else:  # docente
            solicitante = Docente.get_by_id(id_solicitante)
            if solicitante:
                solicitud_dict['solicitante'] = serialize_doc(solicitante)
                solicitud_dict['solicitante']['tipo'] = 'docente'
        
        # Agregar información del convenio
        convenio = Convenio.get_by_id(str(solicitud['id_convenio']))
        if convenio:
            solicitud_dict['convenio'] = serialize_doc(convenio)
        
        # Agregar información de asignaturas
        asignaturas = Asignatura.get_by_solicitud(id_solicitud)
        if asignaturas:
            solicitud_dict['asignaturas'] = serialize_list(asignaturas)
        
        # Agregar información de seguimiento
        seguimiento = Seguimiento.get_by_solicitud(id_solicitud)
        if seguimiento:
            solicitud_dict['seguimiento'] = serialize_doc(seguimiento)
        
        return solicitud_dict, "Solicitud encontrada exitosamente"
    
    @staticmethod
    def get_by_solicitante(id_solicitante, tipo_solicitante='estudiante', page=1, per_page=10):
        """Obtiene todas las solicitudes de un solicitante (estudiante o docente)"""
        filters = {
            'id_solicitante': ObjectId(id_solicitante),
            'tipo_solicitante': tipo_solicitante
        }
        return SolicitudService.get_all(filters, page, per_page)
    
    @staticmethod
    def create(data):
        """Crea una nueva solicitud de intercambio"""
        # Validar que se especifique el tipo de solicitante
        tipo_solicitante = data.get('tipo_solicitante', 'estudiante')
        if tipo_solicitante not in ['estudiante', 'docente']:
            return None, "Tipo de solicitante inválido. Debe ser 'estudiante' o 'docente'"
        
        # Verificar que el solicitante exista según su tipo
        id_solicitante = data['id_solicitante']
        
        if tipo_solicitante == 'estudiante':
            solicitante = Estudiante.get_by_id(id_solicitante)
            if not solicitante:
                return None, "Estudiante no encontrado"
            
            # Verificar que el estudiante cumpla con los requisitos
            cumple, mensaje = Estudiante.cumple_requisitos_intercambio(id_solicitante)
            if not cumple:
                return None, f"El estudiante no cumple con los requisitos: {mensaje}"
        else:  # docente
            solicitante = Docente.get_by_id(id_solicitante)
            if not solicitante:
                return None, "Docente no encontrado"
            
            # Verificar requisitos del docente si existen
            if hasattr(Docente, 'cumple_requisitos_intercambio'):
                cumple, mensaje = Docente.cumple_requisitos_intercambio(id_solicitante)
                if not cumple:
                    return None, f"El docente no cumple con los requisitos: {mensaje}"
        
        # Verificar que el convenio exista
        convenio = Convenio.get_by_id(data['id_convenio'])
        if not convenio:
            return None, "Convenio no encontrado"
        
        # Asegurar que el campo tipo_solicitante está en los datos
        if 'tipo_solicitante' not in data:
            data['tipo_solicitante'] = tipo_solicitante
        
        # Crear la solicitud
        id_solicitud = Solicitud.create(data)
        
        # Si se han incluido asignaturas en la solicitud, crearlas
        if 'asignaturas' in data and isinstance(data['asignaturas'], list):
            for asignatura_data in data['asignaturas']:
                asignatura_data['id_solicitud'] = id_solicitud
                Asignatura.create(asignatura_data)
        
        # Crear un seguimiento inicial para la solicitud
        seguimiento_data = {
            'id_solicitud': id_solicitud,
            'estado_actual': 'pendiente',
            'observaciones': 'Solicitud creada'
        }
        Seguimiento.create(seguimiento_data)
        
        return id_solicitud, "Solicitud creada exitosamente"
    
    @staticmethod
    def update(id_solicitud, data):
        """Actualiza los datos de una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Si se está actualizando el solicitante, verificar que exista según el tipo
        if 'id_solicitante' in data:
            tipo_solicitante = data.get('tipo_solicitante', solicitud.get('tipo_solicitante', 'estudiante'))
            
            if tipo_solicitante == 'estudiante':
                solicitante = Estudiante.get_by_id(data['id_solicitante'])
                if not solicitante:
                    return None, "Estudiante no encontrado"
            else:  # docente
                solicitante = Docente.get_by_id(data['id_solicitante'])
                if not solicitante:
                    return None, "Docente no encontrado"
        
        # Si se está actualizando el tipo de solicitante, validar el valor
        if 'tipo_solicitante' in data:
            if data['tipo_solicitante'] not in ['estudiante', 'docente']:
                return None, "Tipo de solicitante inválido. Debe ser 'estudiante' o 'docente'"
        
        # Si se está actualizando el convenio, verificar que exista
        if 'id_convenio' in data:
            convenio = Convenio.get_by_id(data['id_convenio'])
            if not convenio:
                return None, "Convenio no encontrado"
        
        updated = Solicitud.update(id_solicitud, data)
        return serialize_doc(updated), "Solicitud actualizada exitosamente"
    
    @staticmethod
    def update_estado(id_solicitud, nuevo_estado, comentarios=None):
        """Actualiza el estado de una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Validar estado
        estados_validos = ['pendiente', 'en revision', 'aprobada', 'rechazada', 'finalizada']
        if nuevo_estado not in estados_validos:
            return None, f"Estado no válido. Estados permitidos: {', '.join(estados_validos)}"
        
        updated = Solicitud.update_estado(id_solicitud, nuevo_estado, comentarios)
        
        # Actualizar también el estado del seguimiento
        seguimiento = Seguimiento.get_by_solicitud(id_solicitud)
        if seguimiento:
            estado_seguimiento = 'en proceso' if nuevo_estado == 'aprobada' else nuevo_estado
            Seguimiento.cambiar_estado(str(seguimiento['_id']), estado_seguimiento, comentarios)
        
        return serialize_doc(updated), f"Estado de solicitud actualizado a {nuevo_estado}"
    
    @staticmethod
    def proceso_aprobacion(id_solicitud, nivel_aprobacion, aprobado=True, comentarios=None):
        """Gestiona el proceso de aprobación multinivel de las solicitudes"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        if nivel_aprobacion == 'jefe_programa':
            if aprobado:
                updated = Solicitud.aprobar_jefe_programa(id_solicitud)
                mensaje = "Solicitud aprobada por el jefe de programa"
            else:
                updated = Solicitud.update_estado(id_solicitud, 'rechazada', comentarios)
                mensaje = "Solicitud rechazada por el jefe de programa"
                
        elif nivel_aprobacion == 'consejo_facultad':
            # Solo se puede aprobar si ya fue aprobada por el jefe de programa
            if not solicitud.get('jefe_programa_aprobacion'):
                return None, "La solicitud debe ser aprobada primero por el jefe de programa"
                
            if aprobado:
                updated = Solicitud.aprobar_consejo_facultad(id_solicitud)
                mensaje = "Solicitud aprobada por el consejo de facultad"
            else:
                updated = Solicitud.update_estado(id_solicitud, 'rechazada', comentarios)
                mensaje = "Solicitud rechazada por el consejo de facultad"
                
        elif nivel_aprobacion == 'orpi':
            # Solo se puede aprobar si ya fue aprobada por el consejo de facultad
            if not solicitud.get('consejo_facultad_aprobacion'):
                return None, "La solicitud debe ser aprobada primero por el consejo de facultad"
                
            if aprobado:
                updated, msg = Solicitud.aprobar_ORPI(id_solicitud)
                if not updated:
                    return None, msg
                mensaje = "Solicitud aprobada por la oficina de ORPI"
                
                # Cambiar el estado del seguimiento a 'en proceso'
                seguimiento = Seguimiento.get_by_solicitud(id_solicitud)
                if seguimiento:
                    Seguimiento.cambiar_estado(str(seguimiento['_id']), 'en proceso', 
                                              "Intercambio aprobado y en proceso")
            else:
                updated = Solicitud.update_estado(id_solicitud, 'rechazada', comentarios)
                mensaje = "Solicitud rechazada por la oficina de ORPI"
        else:
            return None, "Nivel de aprobación no válido"
        
        return serialize_doc(updated), mensaje
    
    @staticmethod
    def agregar_documento(id_solicitud, documento):
        """Agrega un documento a la solicitud"""
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        updated = Solicitud.agregar_documento(id_solicitud, documento)
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