import pandas as pd
from models.resultado import Resultado
from models.solicitud import Solicitud
from models.asignatura import Asignatura
from db.db import serialize_doc

class ResultadoService:
    @staticmethod
    def get_by_id(resultado_id):
        """Obtiene un resultado por su ID"""
        resultado = Resultado.get_by_id(resultado_id)
        return serialize_doc(resultado)
    
    @staticmethod
    def importar_csv(archivo_csv, solicitud_id, escala_origen='0-10'):
        try:
            # Verificar si existe la solicitud
            solicitud = Solicitud.get_by_id(solicitud_id)
            if not solicitud:
                return None, "Solicitud no encontrada"
            
            # Leer el archivo CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar estructura del CSV
            if 'codigo_asignatura' in df.columns:
                # Format 1: Usando código de asignatura
                modo = 'codigo'
                if 'nota_obtenida' not in df.columns:
                    return None, "El campo nota_obtenida es requerido en el CSV"
            elif 'asignatura_id' in df.columns:
                # Format 2: Usando ID de asignatura
                modo = 'id'
                if 'nota_obtenida' not in df.columns:
                    return None, "El campo nota_obtenida es requerido en el CSV"
            else:
                return None, "Se requiere el campo codigo_asignatura o asignatura_id en el CSV"
            
            # Procesar cada registro
            resultados = []
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Buscar la asignatura
                    asignatura = None
                    if modo == 'codigo':
                        # Buscar por código
                        asignaturas = Asignatura.get_by_solicitud(solicitud_id)
                        for a in asignaturas:
                            if a['codigo_asignatura_origen'] == row['codigo_asignatura']:
                                asignatura = a
                                break
                        
                        if not asignatura:
                            raise ValueError(f"No se encontró asignatura con código {row['codigo_asignatura']}")
                        
                        asignatura_id = str(asignatura['_id'])
                    else:
                        # Usar ID directamente
                        asignatura_id = row['asignatura_id']
                        asignatura = Asignatura.get_by_id(asignatura_id)
                        
                        if not asignatura:
                            raise ValueError(f"No se encontró asignatura con ID {asignatura_id}")
                    
                    # Verificar que la asignatura pertenezca a la solicitud
                    if str(asignatura['solicitud_id']) != solicitud_id:
                        raise ValueError("La asignatura no pertenece a esta solicitud")
                    
                    # Verificar si ya existe un resultado para esta asignatura
                    existing = Resultado.get_by_asignatura(asignatura_id)
                    if existing:
                        errores.append({
                            'fila': index + 2,
                            'error': "Ya existe un resultado para esta asignatura",
                            'datos': row.to_dict()
                        })
                        continue
                    
                    # Crear resultado
                    nota_obtenida = float(row['nota_obtenida'])
                    nota_convertida = Resultado.convertir_nota(nota_obtenida, escala_origen)
                    
                    resultado_data = {
                        'solicitud_id': solicitud_id,
                        'asignatura_id': asignatura_id,
                        'nota_obtenida': nota_obtenida,
                        'nota_convertida': nota_convertida,
                        'escala_origen': escala_origen,
                        'estado_homologacion': 'pendiente',
                        'observaciones': row.get('observaciones', '')
                    }
                    
                    # Insertar en la base de datos
                    resultado_id = Resultado.create(resultado_data)
                    resultados.append(resultado_id)
                    
                except Exception as e:
                    # Registrar error para este registro
                    errores.append({
                        'fila': index + 2,
                        'error': str(e),
                        'datos': row.to_dict()
                    })
            
            return {
                'total_importados': len(resultados),
                'resultados_creados': resultados,
                'errores': errores
            }, "Resultados importados con éxito"
        
        except Exception as e:
            return None, f"Error al procesar el archivo CSV: {str(e)}"
    
    @staticmethod
    def get_by_solicitud(solicitud_id):
        """Obtiene todos los resultados para una solicitud específica"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        resultados = Resultado.get_by_solicitud(solicitud_id)
        
        # Enriquecer con información de asignaturas
        resultados_enriquecidos = []
        for resultado in resultados:
            resultado_dict = serialize_doc(resultado)
            
            # Agregar información de la asignatura
            asignatura = Asignatura.get_by_id(str(resultado['asignatura_id']))
            if asignatura:
                resultado_dict['asignatura'] = {
                    'codigo_origen': asignatura.get('codigo_asignatura_origen'),
                    'nombre_origen': asignatura.get('nombre_asignatura_origen'),
                    'codigo_destino': asignatura.get('codigo_asignatura_destino'),
                    'nombre_destino': asignatura.get('nombre_asignatura_destino')
                }
            
            resultados_enriquecidos.append(resultado_dict)
        
        return resultados_enriquecidos, "Resultados encontrados exitosamente"
    
    @staticmethod
    def get_by_asignatura(asignatura_id):
        """Obtiene el resultado para una asignatura específica"""
        # Verificar si existe la asignatura
        asignatura = Asignatura.get_by_id(asignatura_id)
        if not asignatura:
            return None, "Asignatura no encontrada"
        
        resultado = Resultado.get_by_asignatura(asignatura_id)
        return serialize_doc(resultado), "Resultado encontrado exitosamente"
    
    @staticmethod
    def create(data):
        """Crea un nuevo resultado de intercambio para una asignatura"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(data['solicitud_id'])
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        # Verificar si existe la asignatura
        asignatura = Asignatura.get_by_id(data['asignatura_id'])
        if not asignatura:
            return None, "Asignatura no encontrada"
        
        # Verificar que la asignatura pertenezca a la solicitud
        if str(asignatura['solicitud_id']) != data['solicitud_id']:
            return None, "La asignatura no pertenece a esta solicitud"
        
        # Verificar si ya existe un resultado para esta asignatura
        existing = Resultado.get_by_asignatura(data['asignatura_id'])
        if existing:
            return None, "Ya existe un resultado para esta asignatura"
        
        # Validar campos requeridos
        if 'nota_obtenida' not in data or data['nota_obtenida'] is None:
            return None, "La nota obtenida es requerida"
        
        if 'escala_origen' not in data or not data['escala_origen']:
            return None, "La escala de origen es requerida"
        
        # Convertir la nota al sistema de la UPC si no se proporciona
        if 'nota_convertida' not in data or data['nota_convertida'] is None:
            data['nota_convertida'] = Resultado.convertir_nota(
                data['nota_obtenida'], data['escala_origen']
            )
        
        resultado_id = Resultado.create(data)
        return resultado_id, "Resultado creado exitosamente"
    
    @staticmethod
    def update(resultado_id, data):
        """Actualiza los datos de un resultado"""
        # Verificar si existe el resultado
        resultado = Resultado.get_by_id(resultado_id)
        if not resultado:
            return None, "Resultado no encontrado"
        
        # Si se está cambiando la asignatura, verificar que exista y pertenezca a la solicitud
        if 'asignatura_id' in data:
            asignatura = Asignatura.get_by_id(data['asignatura_id'])
            if not asignatura:
                return None, "Asignatura no encontrada"
            
            # Si también se está cambiando la solicitud, verificar relación
            if 'solicitud_id' in data:
                if str(asignatura['solicitud_id']) != data['solicitud_id']:
                    return None, "La asignatura no pertenece a esta solicitud"
            else:
                # Verificar con la solicitud actual
                if str(asignatura['solicitud_id']) != str(resultado['solicitud_id']):
                    return None, "La asignatura no pertenece a esta solicitud"
        
        # Si se cambia la nota, recalcular la conversión
        if ('nota_obtenida' in data and data['nota_obtenida'] is not None and 
            'nota_convertida' not in data):
            
            escala_origen = data.get('escala_origen', resultado.get('escala_origen', '0-5'))
            data['nota_convertida'] = Resultado.convertir_nota(
                data['nota_obtenida'], escala_origen
            )
        
        updated = Resultado.update(resultado_id, data)
        return serialize_doc(updated), "Resultado actualizado exitosamente"
    
    @staticmethod
    def aprobar_homologacion(resultado_id, aprobado_por=None, observaciones=None):
        """Aprueba la homologación de una nota"""
        # Verificar si existe el resultado
        resultado = Resultado.get_by_id(resultado_id)
        if not resultado:
            return None, "Resultado no encontrado"
        
        updated = Resultado.aprobar_homologacion(resultado_id, aprobado_por, observaciones)
        
        # Verificar si todos los resultados de la solicitud están homologados
        solicitud_id = str(resultado['solicitud_id'])
        todos_homologados = Resultado.verificar_todos_homologados(solicitud_id)
        
        mensaje_adicional = ""
        if todos_homologados:
            mensaje_adicional = " Todos los resultados de esta solicitud han sido homologados."
            
            # Actualizar el seguimiento y la solicitud
            seguimiento = seguimiento.get_by_solicitud(solicitud_id)
            if seguimiento:
                seguimiento.cambiar_estado(str(seguimiento['_id']), 'finalizado', 
                                          "Intercambio finalizado con éxito")
            
            Solicitud.update_estado(solicitud_id, 'finalizada', 
                                  "Intercambio finalizado con éxito")
        
        return serialize_doc(updated), f"Homologación aprobada exitosamente.{mensaje_adicional}"
    
    @staticmethod
    def rechazar_homologacion(resultado_id, motivo, rechazado_por=None):
        """Rechaza la homologación de una nota"""
        # Verificar si existe el resultado
        resultado = Resultado.get_by_id(resultado_id)
        if not resultado:
            return None, "Resultado no encontrado"
        
        updated = Resultado.rechazar_homologacion(resultado_id, motivo, rechazado_por)
        return serialize_doc(updated), "Homologación rechazada exitosamente"
    
    @staticmethod
    def get_promedio_intercambio(solicitud_id):
        """Calcula el promedio de las notas homologadas para una solicitud"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(solicitud_id)
        if not solicitud:
            return None, "Solicitud no encontrada"
        
        promedio = Resultado.get_promedio_intercambio(solicitud_id)
        return promedio, "Promedio calculado exitosamente"