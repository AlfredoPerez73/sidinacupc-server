import pandas as pd
from datetime import datetime
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
    def importar_csv(archivo_csv):
        try:
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar estructura del CSV
            campos_requeridos = ['nombre_institucion', 'pais_institucion', 'tipo_convenio', 'fecha_inicio', 'fecha_fin']
            for campo in campos_requeridos:
                if campo not in df.columns:
                    return None, f"El campo {campo} es requerido en el CSV"
            
            # Procesar cada registro
            resultados = []
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Convertir fechas
                    try:
                        fecha_inicio = datetime.strptime(row['fecha_inicio'], '%Y-%m-%d')
                        fecha_fin = datetime.strptime(row['fecha_fin'], '%Y-%m-%d')
                    except ValueError:
                        raise ValueError("Formato de fecha incorrecto. Use YYYY-MM-DD")
                    
                    # Crear convenio
                    convenio_data = {
                        'nombre_institucion': row['nombre_institucion'],
                        'pais_institucion': row['pais_institucion'],
                        'ciudad_institucion': row.get('ciudad_institucion', ''),
                        'tipo_convenio': row['tipo_convenio'],
                        'fecha_inicio': fecha_inicio,
                        'fecha_fin': fecha_fin,
                        'estado': row.get('estado', 'activo'),
                        'descripcion': row.get('descripcion', ''),
                        'requisitos_especificos': row.get('requisitos_especificos', ''),
                        'beneficios': row.get('beneficios', ''),
                        'cupos_disponibles': int(row.get('cupos_disponibles', 0))
                    }
                    
                    # Si hay datos de contacto
                    if 'contacto_nombre' in row and row['contacto_nombre']:
                        convenio_data['contacto_institucion'] = {
                            'nombre': row['contacto_nombre'],
                            'cargo': row.get('contacto_cargo', ''),
                            'email': row.get('contacto_email', ''),
                            'telefono': row.get('contacto_telefono', '')
                        }
                    
                    # Insertar en la base de datos
                    id_convenio = Convenio.create(convenio_data)
                    resultados.append(id_convenio)
                    
                except Exception as e:
                    # Registrar error para este registro
                    errores.append({
                        'fila': index + 2,
                        'error': str(e),
                        'datos': row.to_dict()
                    })
            
            return {
                'total_importados': len(resultados),
                'convenios_creados': resultados,
                'errores': errores
            }, "Convenios importados con éxito"
        
        except Exception as e:
            return None, f"Error al procesar el archivo CSV: {str(e)}"
    
    @staticmethod
    def get_by_id(id_convenio):
        """Obtiene un convenio por su ID"""
        convenio = Convenio.get_by_id(id_convenio)
        return serialize_doc(convenio)
    
    @staticmethod
    def create(data):
        """Crea un nuevo convenio"""
        id_convenio = Convenio.create(data)
        return id_convenio, "Convenio creado exitosamente"
    
    @staticmethod
    def update(id_convenio, data):
        """Actualiza los datos de un convenio"""
        # Verificar si existe el convenio
        convenio = Convenio.get_by_id(id_convenio)
        if not convenio:
            return None, "Convenio no encontrado"
        
        updated = Convenio.update(id_convenio, data)
        return serialize_doc(updated), "Convenio actualizado exitosamente"
    
    @staticmethod
    def delete(id_convenio):
        """Elimina un convenio (cambia su estado a inactivo)"""
        # Verificar si existe el convenio
        convenio = Convenio.get_by_id(id_convenio)
        if not convenio:
            return False, "Convenio no encontrado"
        
        Convenio.delete(id_convenio)
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