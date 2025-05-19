import pandas as pd
from models.docente import Docente
from bson import ObjectId
from db.db import serialize_doc, serialize_list
import logging

logger = logging.getLogger(__name__)

class DocenteService:
    @staticmethod
    def crear_docente(data):
        """Servicio para crear un nuevo docente"""
        try:
            # Validar datos obligatorios
            required_fields = [
                'nombre_completo', 'documento_identidad', 'email', 
                'departamento', 'facultad', 'categoria_docente', 'tipo_vinculacion'
            ]
            
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'El campo {field} es obligatorio',
                        'data': None
                    }
            
            # Verificar que no exista otro docente con el mismo documento
            existing_docente = Docente.get_by_documento(data['documento_identidad'])
            if existing_docente:
                return {
                    'success': False,
                    'message': 'Ya existe un docente con este número de documento',
                    'data': None
                }
            
            # Crear el docente
            id_docente = Docente.create(data)
            docente = Docente.get_by_id(id_docente)
            
            return {
                'success': True,
                'message': 'Docente creado exitosamente',
                'data': docente
            }
            
        except Exception as e:
            logger.error(f"Error creando docente: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def importar_csv(archivo_csv):
        """Servicio para importar docentes desde un archivo CSV"""
        try:
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar estructura del CSV
            campos_requeridos = ['nombre_completo', 'documento_identidad', 'email', 
                               'departamento', 'facultad', 'categoria_docente']
            for campo in campos_requeridos:
                if campo not in df.columns:
                    return {
                        'success': False,
                        'message': f"El campo {campo} es requerido en el CSV",
                        'data': None
                    }
            
            # Procesar cada registro
            resultados = []
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Verificar si ya existe un docente con el mismo documento
                    existing = Docente.get_by_documento(str(row['documento_identidad']))
                    if existing:
                        errores.append({
                            'fila': index + 2,
                            'error': "Ya existe un docente con este documento de identidad",
                            'datos': row.to_dict()
                        })
                        continue
                    
                    # Crear docente
                    docente_data = {
                        'nombre_completo': row['nombre_completo'],
                        'documento_identidad': str(row['documento_identidad']),
                        'tipo_documento': row.get('tipo_documento', 'CC'),
                        'email': row['email'],
                        'telefono': str(row.get('telefono', '')),
                        'departamento': row['departamento'],
                        'facultad': row['facultad'],
                        'categoria_docente': row['categoria_docente'],
                        'tipo_vinculacion': row.get('tipo_vinculacion', 'Planta'),
                        'titulo_pregrado': row.get('titulo_pregrado', ''),
                        'titulo_posgrado': row.get('titulo_posgrado', ''),
                        'nivel_formacion': row.get('nivel_formacion', 'Pregrado'),
                        'anos_experiencia': int(row.get('anos_experiencia', 0)),
                        'anos_experiencia_institucion': int(row.get('anos_experiencia_institucion', 0)),
                        'escalafon': row.get('escalafon', ''),
                        'evaluacion_docente_promedio': float(row.get('evaluacion_docente_promedio', 0)),
                        'publicaciones': int(row.get('publicaciones', 0)),
                        'proyectos_investigacion': int(row.get('proyectos_investigacion', 0)),
                        'estado': 'activo',
                        'sanciones_academicas': False,
                        'sanciones_disciplinarias': False,
                        'experiencia_internacional': False
                    }
                    
                    # Insertar en la base de datos
                    id_docente = Docente.create(docente_data)
                    resultados.append(id_docente)
                    
                except Exception as e:
                    # Registrar error para este registro
                    errores.append({
                        'fila': index + 2,  # +2 por encabezado y base 0
                        'error': str(e),
                        'datos': row.to_dict()
                    })
            
            return {
                'success': True,
                'message': 'Docentes importados con éxito',
                'data': {
                    'total_importados': len(resultados),
                    'docentes_creados': resultados,
                    'errores': errores
                }
            }
        
        except Exception as e:
            logger.error(f"Error procesando CSV: {str(e)}")
            return {
                'success': False,
                'message': f"Error al procesar el archivo CSV: {str(e)}",
                'data': None
            }
    
    @staticmethod
    def obtener_por_documento(documento):
        """Servicio para obtener un docente por su documento de identidad"""
        try:
            docente = Docente.get_by_documento(documento)
            
            if not docente:
                return {
                    'success': False,
                    'message': 'Docente no encontrado',
                    'data': None
                }
            
            return {
                'success': True,
                'message': 'Docente encontrado',
                'data': serialize_doc(docente)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo docente por documento: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def buscar_por_nombre(nombre, page=1, per_page=10):
        """Servicio para buscar docentes por nombre"""
        try:
            filters = {'nombre_completo': {'$regex': nombre, '$options': 'i'}}
            result = Docente.get_all(filters, page, per_page)
            
            return {
                'success': True,
                'message': 'Búsqueda completada',
                'data': {
                    'docentes': serialize_list(result['docentes']),
                    'total': result['total'],
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'pages': result['pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error buscando docentes por nombre: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def obtener_estadisticas():
        """Servicio para obtener estadísticas de docentes"""
        try:
            # Pipeline de agregación para obtener estadísticas
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total_docentes': {'$sum': 1},
                        'activos': {
                            '$sum': {
                                '$cond': [{'$eq': ['$estado', 'activo']}, 1, 0]
                            }
                        },
                        'inactivos': {
                            '$sum': {
                                '$cond': [{'$eq': ['$estado', 'inactivo']}, 1, 0]
                            }
                        },
                        'por_categoria': {
                            '$push': '$categoria_docente'
                        },
                        'por_departamento': {
                            '$push': '$departamento'
                        },
                        'por_vinculacion': {
                            '$push': '$tipo_vinculacion'
                        },
                        'promedio_experiencia': {
                            '$avg': '$anos_experiencia'
                        },
                        'promedio_evaluacion': {
                            '$avg': '$evaluacion_docente_promedio'
                        }
                    }
                }
            ]
            
            # Ejecutar agregación
            from db.db import mongo
            result = list(mongo.db.docentes.aggregate(pipeline))
            
            if not result:
                return {
                    'success': True,
                    'message': 'No hay datos disponibles',
                    'data': {
                        'total_docentes': 0,
                        'activos': 0,
                        'inactivos': 0,
                        'por_categoria': {},
                        'por_departamento': {},
                        'por_vinculacion': {},
                        'promedio_experiencia': 0,
                        'promedio_evaluacion': 0
                    }
                }
            
            stats = result[0]
            
            # Procesar conteos por categoría
            from collections import Counter
            categoria_counts = Counter(stats['por_categoria'])
            departamento_counts = Counter(stats['por_departamento'])
            vinculacion_counts = Counter(stats['por_vinculacion'])
            
            return {
                'success': True,
                'message': 'Estadísticas obtenidas exitosamente',
                'data': {
                    'total_docentes': stats['total_docentes'],
                    'activos': stats['activos'],
                    'inactivos': stats['inactivos'],
                    'por_categoria': dict(categoria_counts),
                    'por_departamento': dict(departamento_counts),
                    'por_vinculacion': dict(vinculacion_counts),
                    'promedio_experiencia': round(stats.get('promedio_experiencia', 0), 2),
                    'promedio_evaluacion': round(stats.get('promedio_evaluacion', 0), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def obtener_docente(id_docente):
        """Servicio para obtener un docente por ID"""
        try:
            if not ObjectId.is_valid(id_docente):
                return {
                    'success': False,
                    'message': 'ID de docente inválido',
                    'data': None
                }
            
            docente = Docente.get_by_id(id_docente)
            if not docente:
                return {
                    'success': False,
                    'message': 'Docente no encontrado',
                    'data': None
                }
            
            return {
                'success': True,
                'message': 'Docente encontrado',
                'data': serialize_doc(docente)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo docente: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def actualizar_docente(id_docente, data):
        """Servicio para actualizar un docente"""
        try:
            if not ObjectId.is_valid(id_docente):
                return {
                    'success': False,
                    'message': 'ID de docente inválido',
                    'data': None
                }
            
            # Verificar que el docente existe
            existing_docente = Docente.get_by_id(id_docente)
            if not existing_docente:
                return {
                    'success': False,
                    'message': 'Docente no encontrado',
                    'data': None
                }
            
            # Si se está actualizando el documento, verificar que no exista otro docente con ese documento
            if 'documento_identidad' in data:
                other_docente = Docente.get_by_documento(data['documento_identidad'])
                if other_docente and str(other_docente['_id']) != id_docente:
                    return {
                        'success': False,
                        'message': 'Ya existe otro docente con este número de documento',
                        'data': None
                    }
            
            # Actualizar el docente
            docente = Docente.update(id_docente, data)
            
            return {
                'success': True,
                'message': 'Docente actualizado exitosamente',
                'data': serialize_doc(docente)
            }
            
        except Exception as e:
            logger.error(f"Error actualizando docente: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def eliminar_docente(id_docente):
        """Servicio para eliminar (inactivar) un docente"""
        try:
            if not ObjectId.is_valid(id_docente):
                return {
                    'success': False,
                    'message': 'ID de docente inválido',
                    'data': None
                }
            
            # Verificar que el docente existe
            existing_docente = Docente.get_by_id(id_docente)
            if not existing_docente:
                return {
                    'success': False,
                    'message': 'Docente no encontrado',
                    'data': None
                }
            
            # Eliminar (inactivar) el docente
            Docente.delete(id_docente)
            
            return {
                'success': True,
                'message': 'Docente eliminado exitosamente',
                'data': None
            }
            
        except Exception as e:
            logger.error(f"Error eliminando docente: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def listar_docentes(page=1, per_page=10, filters=None):
        """Servicio para listar docentes con paginación y filtros"""
        try:
            if filters is None:
                filters = {}
            
            # Construir filtros de búsqueda
            search_filters = {}
            
            if 'estado' in filters:
                search_filters['estado'] = filters['estado']
            
            if 'departamento' in filters:
                search_filters['departamento'] = filters['departamento']
            
            if 'facultad' in filters:
                search_filters['facultad'] = filters['facultad']
            
            if 'categoria_docente' in filters:
                search_filters['categoria_docente'] = filters['categoria_docente']
            
            if 'tipo_vinculacion' in filters:
                search_filters['tipo_vinculacion'] = filters['tipo_vinculacion']
            
            if 'nombre' in filters:
                search_filters['nombre_completo'] = {
                    '$regex': filters['nombre'], 
                    '$options': 'i'
                }
            
            result = Docente.get_all(search_filters, page, per_page)
            
            # Serializar los resultados
            return {
                'success': True,
                'message': 'Lista de docentes obtenida exitosamente',
                'data': {
                    'docentes': serialize_list(result['docentes']),
                    'total': result['total'],
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'pages': result['pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error listando docentes: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def verificar_requisitos_intercambio(id_docente):
        """Servicio para verificar si un docente cumple requisitos de intercambio"""
        try:
            if not ObjectId.is_valid(id_docente):
                return {
                    'success': False,
                    'message': 'ID de docente inválido',
                    'data': None
                }
            
            cumple, mensaje = Docente.cumple_requisitos_intercambio(id_docente)
            
            return {
                'success': True,
                'message': 'Verificación completada',
                'data': {
                    'cumple_requisitos': cumple,
                    'detalles': mensaje
                }
            }
            
        except Exception as e:
            logger.error(f"Error verificando requisitos: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def obtener_docentes_elegibles():
        """Servicio para obtener docentes elegibles para intercambio"""
        try:
            docentes_elegibles = Docente.get_docentes_elegibles_intercambio()
            
            return {
                'success': True,
                'message': f'Se encontraron {len(docentes_elegibles)} docentes elegibles',
                'data': {
                    'docentes': serialize_list(docentes_elegibles),
                    'total': len(docentes_elegibles)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo docentes elegibles: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def obtener_por_departamento(departamento):
        """Servicio para obtener docentes por departamento"""
        try:
            docentes = Docente.get_by_departamento(departamento)
            
            return {
                'success': True,
                'message': f'Docentes del departamento {departamento}',
                'data': {
                    'docentes': serialize_list(docentes),
                    'total': len(docentes)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo docentes por departamento: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }
    
    @staticmethod
    def registrar_experiencia_internacional(id_docente, experiencia_data):
        """Servicio para registrar experiencia internacional de un docente"""
        try:
            if not ObjectId.is_valid(id_docente):
                return {
                    'success': False,
                    'message': 'ID de docente inválido',
                    'data': None
                }
            
            # Validar datos obligatorios de la experiencia
            required_fields = ['institucion', 'pais', 'tipo_intercambio', 'fecha_inicio', 'fecha_fin']
            for field in required_fields:
                if not experiencia_data.get(field):
                    return {
                        'success': False,
                        'message': f'El campo {field} es obligatorio',
                        'data': None
                    }
            
            success = Docente.actualizar_experiencia_internacional(id_docente, experiencia_data)
            
            if success:
                return {
                    'success': True,
                    'message': 'Experiencia internacional registrada exitosamente',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo registrar la experiencia internacional',
                    'data': None
                }
            
        except Exception as e:
            logger.error(f"Error registrando experiencia internacional: {str(e)}")
            return {
                'success': False,
                'message': 'Error interno del servidor',
                'data': None
            }