import pandas as pd
from models.asignatura import Asignatura
from models.solicitud import Solicitud
from db.db import serialize_doc, serialize_list

class AsignaturaService:
    @staticmethod
    def get_by_id(asignatura_id):
        """Obtiene una asignatura por su ID"""
        asignatura = Asignatura.get_by_id(asignatura_id)
        return serialize_doc(asignatura)
    
    @staticmethod
    def importar_csv(archivo_csv, solicitud_id):
        try:
            # Verificar si existe la solicitud
            solicitud = Solicitud.get_by_id(solicitud_id)
            if not solicitud:
                return None, "Solicitud no encontrada"
            
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar estructura del CSV
            campos_requeridos = [
                'codigo_asignatura_origen', 'nombre_asignatura_origen', 'creditos_asignatura_origen',
                'codigo_asignatura_destino', 'nombre_asignatura_destino', 'creditos_asignatura_destino'
            ]
            for campo in campos_requeridos:
                if campo not in df.columns:
                    return None, f"El campo {campo} es requerido en el CSV"
            
            # Procesar cada registro
            resultados = []
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Crear asignatura
                    asignatura_data = {
                        'solicitud_id': solicitud_id,
                        'codigo_asignatura_origen': row['codigo_asignatura_origen'],
                        'nombre_asignatura_origen': row['nombre_asignatura_origen'],
                        'creditos_asignatura_origen': float(row['creditos_asignatura_origen']),
                        'codigo_asignatura_destino': row['codigo_asignatura_destino'],
                        'nombre_asignatura_destino': row['nombre_asignatura_destino'],
                        'creditos_asignatura_destino': float(row['creditos_asignatura_destino']),
                        'estado_equivalencia': 'propuesta',
                        'observaciones': row.get('observaciones', '')
                    }
                    
                    # Insertar en la base de datos
                    asignatura_id = Asignatura.create(asignatura_data)
                    resultados.append(asignatura_id)
                    
                except Exception as e:
                    # Registrar error para este registro
                    errores.append({
                        'fila': index + 2,
                        'error': str(e),
                        'datos': row.to_dict()
                    })
            
            return {
                'total_importados': len(resultados),
                'asignaturas_creadas': resultados,
                'errores': errores
            }, "Asignaturas importadas con éxito"
        
        except Exception as e:
            return None, f"Error al procesar el archivo CSV: {str(e)}"
    
    @staticmethod
    def get_by_solicitud(solicitud_id):
        """Obtiene todas las asignaturas para una solicitud específica"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        asignaturas = Asignatura.get_by_solicitud(solicitud_id)
        return serialize_list(asignaturas), "Asignaturas encontradas exitosamente"
    
    @staticmethod
    def create(data):
        """Crea una nueva equivalencia de asignatura"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(data['solicitud_id'])
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Validar campos requeridos
        required_fields = ['codigo_asignatura_origen', 'nombre_asignatura_origen',
                           'creditos_asignatura_origen', 'codigo_asignatura_destino',
                           'nombre_asignatura_destino', 'creditos_asignatura_destino']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return None, f"El campo {field} es requerido"
        
        asignatura_id = Asignatura.create(data)
        return asignatura_id, "Asignatura creada exitosamente"
    
    @staticmethod
    def update(asignatura_id, data):
        """Actualiza los datos de una asignatura"""
        # Verificar si existe la asignatura
        asignatura = Asignatura.get_by_id(asignatura_id)
        if not asignatura:
            return None, "Asignatura no encontrada"
        
        # Si se está cambiando la solicitud, verificar que exista
        if 'solicitud_id' in data:
            solicitud = Solicitud.get_by_id(data['solicitud_id'])
            if not solicitud:
                return None, "Solicitud no encontrada"
        
        updated = Asignatura.update(asignatura_id, data)
        return serialize_doc(updated), "Asignatura actualizada exitosamente"
    
    @staticmethod
    def delete(asignatura_id):
        """Elimina una asignatura"""
        # Verificar si existe la asignatura
        asignatura = Asignatura.get_by_id(asignatura_id)
        if not asignatura:
            return False, "Asignatura no encontrada"
        
        success = Asignatura.delete(asignatura_id)
        return success, "Asignatura eliminada exitosamente" if success else "Error al eliminar asignatura"
    
    @staticmethod
    def aprobar_equivalencia(asignatura_id, aprobado_por):
        """Aprueba una equivalencia de asignatura"""
        # Verificar si existe la asignatura
        asignatura = Asignatura.get_by_id(asignatura_id)
        if not asignatura:
            return None, "Asignatura no encontrada"
        
        updated = Asignatura.aprobar_equivalencia(asignatura_id, aprobado_por)
        
        # Verificar si todas las asignaturas de la solicitud están aprobadas
        solicitud_id = str(asignatura['solicitud_id'])
        todas_aprobadas = Asignatura.verificar_todas_aprobadas(solicitud_id)
        
        mensaje_adicional = ""
        if todas_aprobadas:
            mensaje_adicional = " Todas las asignaturas de esta solicitud han sido aprobadas."
        
        return serialize_doc(updated), f"Equivalencia aprobada exitosamente.{mensaje_adicional}"
    
    @staticmethod
    def rechazar_equivalencia(asignatura_id, observaciones, aprobado_por):
        """Rechaza una equivalencia de asignatura"""
        # Verificar si existe la asignatura
        asignatura = Asignatura.get_by_id(asignatura_id)
        if not asignatura:
            return None, "Asignatura no encontrada"
        
        updated = Asignatura.rechazar_equivalencia(asignatura_id, observaciones, aprobado_por)
        return serialize_doc(updated), "Equivalencia rechazada exitosamente"
    
    @staticmethod
    def obtener_total_creditos(solicitud_id):
        """Obtiene el total de créditos de las asignaturas aprobadas para una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        total_creditos = Asignatura.obtener_total_creditos(solicitud_id)
        return total_creditos, "Total de créditos calculado exitosamente"