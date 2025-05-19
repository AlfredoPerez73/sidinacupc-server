import pandas as pd
from models.estudiante import Estudiante
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
    def importar_csv(archivo_csv):
        try:
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar estructura del CSV
            campos_requeridos = ['nombre_completo', 'documento_identidad', 'programa_academico']
            for campo in campos_requeridos:
                if campo not in df.columns:
                    return None, f"El campo {campo} es requerido en el CSV"
            
            # Procesar cada registro
            resultados = []
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Verificar si ya existe un estudiante con el mismo documento
                    existing = Estudiante.get_by_documento(str(row['documento_identidad']))
                    if existing:
                        errores.append({
                            'fila': index + 2,
                            'error': "Ya existe un estudiante con este documento de identidad",
                            'datos': row.to_dict()
                        })
                        continue
                    
                    # Crear estudiante
                    estudiante_data = {
                        'nombre_completo': row['nombre_completo'],
                        'documento_identidad': str(row['documento_identidad']),
                        'tipo_documento': row.get('tipo_documento', 'CC'),
                        'programa_academico': row['programa_academico'],
                        'facultad': row.get('facultad'),
                        'email': row.get('email'),
                        'telefono': str(row.get('telefono', '')),
                        'creditos_cursados': float(row.get('creditos_cursados', 0)),
                        'promedio_academico': float(row.get('promedio_academico', 0)),
                        'estado': 'activo',
                        'sanciones_academicas': False,
                        'sanciones_disciplinarias': False
                    }
                    
                    # Insertar en la base de datos
                    id_estudiante = Estudiante.create(estudiante_data)
                    resultados.append(id_estudiante)
                    
                except Exception as e:
                    # Registrar error para este registro
                    errores.append({
                        'fila': index + 2,  # +2 por encabezado y base 0
                        'error': str(e),
                        'datos': row.to_dict()
                    })
            
            return {
                'total_importados': len(resultados),
                'estudiantes_creados': resultados,
                'errores': errores
            }, "Estudiantes importados con éxito"
        
        except Exception as e:
            return None, f"Error al procesar el archivo CSV: {str(e)}"
    
    @staticmethod
    def get_by_id(id_estudiante):
        """Obtiene un estudiante por su ID"""
        estudiante = Estudiante.get_by_id(id_estudiante)
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
        
        id_estudiante = Estudiante.create(data)
        return id_estudiante, "Estudiante creado exitosamente"
    
    @staticmethod
    def update(id_estudiante, data):
        """Actualiza los datos de un estudiante"""
        # Verificar si existe el estudiante
        estudiante = Estudiante.get_by_id(id_estudiante)
        if not estudiante:
            return None, "Estudiante no encontrado"
        
        # Si se está actualizando el documento, verificar que no exista otro con ese documento
        if 'documento_identidad' in data:
            existing = Estudiante.get_by_documento(data['documento_identidad'])
            if existing and str(existing['_id']) != id_estudiante:
                return None, "Ya existe otro estudiante con este documento de identidad"
        
        updated = Estudiante.update(id_estudiante, data)
        return serialize_doc(updated), "Estudiante actualizado exitosamente"
    
    @staticmethod
    def delete(id_estudiante):
        """Elimina un estudiante (cambia su estado a inactivo)"""
        # Verificar si existe el estudiante
        estudiante = Estudiante.get_by_id(id_estudiante)
        if not estudiante:
            return False, "Estudiante no encontrado"
        
        Estudiante.delete(id_estudiante)
        return True, "Estudiante eliminado exitosamente"
    
    @staticmethod
    def verificar_requisitos(id_estudiante):
        """Verifica si un estudiante cumple con los requisitos para intercambio"""
        # Verificar si existe el estudiante
        estudiante = Estudiante.get_by_id(id_estudiante)
        if not estudiante:
            return False, "Estudiante no encontrado"
        
        cumple, mensaje = Estudiante.cumple_requisitos_intercambio(id_estudiante)
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
        
