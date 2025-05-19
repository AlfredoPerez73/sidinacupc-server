from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Resultado:
    @staticmethod
    def create(data):
        """Crea un nuevo resultado de intercambio para una asignatura"""
        resultado = {
            'id_solicitud': ObjectId(data.get('id_solicitud')),
            'id_asignatura': ObjectId(data.get('id_asignatura')),
            'nota_obtenida': data.get('nota_obtenida'),
            'nota_convertida': data.get('nota_convertida'),  # Nota convertida al sistema de la UPC
            'escala_origen': data.get('escala_origen', ''),  # Ej: "0-100", "0-10", "A-F"
            'fecha_registro': data.get('fecha_registro', datetime.utcnow()),
            'documento_soporte': data.get('documento_soporte'),
            'estado_homologacion': data.get('estado_homologacion', 'pendiente'),
            'observaciones': data.get('observaciones', ''),
            'registrado_por': data.get('registrado_por'),
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.resultados.insert_one(resultado)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(resultado_id):
        """Obtiene un resultado por su ID"""
        return mongo.db.resultados.find_one({'_id': ObjectId(resultado_id)})
    
    @staticmethod
    def get_by_solicitud(id_solicitud):
        """Obtiene todos los resultados para una solicitud específica"""
        return list(mongo.db.resultados.find({'id_solicitud': ObjectId(id_solicitud)}))
    
    @staticmethod
    def get_by_asignatura(id_asignatura):
        """Obtiene el resultado para una asignatura específica"""
        return mongo.db.resultados.find_one({'id_asignatura': ObjectId(id_asignatura)})
    
    @staticmethod
    def update(resultado_id, data):
        """Actualiza los datos de un resultado"""
        # Convertir IDs a ObjectId si están presentes
        if 'id_solicitud' in data:
            data['id_solicitud'] = ObjectId(data['id_solicitud'])
        if 'id_asignatura' in data:
            data['id_asignatura'] = ObjectId(data['id_asignatura'])
        
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.resultados.update_one(
            {'_id': ObjectId(resultado_id)},
            {'$set': data}
        )
        
        return Resultado.get_by_id(resultado_id)
    
    @staticmethod
    def aprobar_homologacion(resultado_id, aprobado_por=None, observaciones=None):
        """Aprueba la homologación de una nota"""
        update_data = {
            'estado_homologacion': 'aprobada',
            'fecha_actualizacion': datetime.utcnow()
        }
        
        if aprobado_por:
            update_data['registrado_por'] = aprobado_por
            
        if observaciones:
            update_data['observaciones'] = observaciones
        
        mongo.db.resultados.update_one(
            {'_id': ObjectId(resultado_id)},
            {'$set': update_data}
        )
        
        return Resultado.get_by_id(resultado_id)
    
    @staticmethod
    def rechazar_homologacion(resultado_id, motivo, rechazado_por=None):
        """Rechaza la homologación de una nota"""
        update_data = {
            'estado_homologacion': 'rechazada',
            'observaciones': motivo,
            'fecha_actualizacion': datetime.utcnow()
        }
        
        if rechazado_por:
            update_data['registrado_por'] = rechazado_por
        
        mongo.db.resultados.update_one(
            {'_id': ObjectId(resultado_id)},
            {'$set': update_data}
        )
        
        return Resultado.get_by_id(resultado_id)
    
    @staticmethod
    def verificar_todos_homologados(id_solicitud):
        """Verifica si todos los resultados de una solicitud están homologados"""
        resultados = Resultado.get_by_solicitud(id_solicitud)
        
        if not resultados:
            return False
        
        for resultado in resultados:
            if resultado.get('estado_homologacion') != 'aprobada':
                return False
        
        return True
    
    @staticmethod
    def convertir_nota(nota_origen, escala_origen, escala_destino="0-5"):
        """Convierte una nota desde una escala extranjera a la escala de la UPC (0-5)"""
        # Implementación básica para algunas escalas comunes
        # En una implementación completa, esto sería más sofisticado
        
        if escala_origen == escala_destino:
            return nota_origen
        
        # Convertir desde escala 0-10 a escala 0-5
        if escala_origen == "0-10" and escala_destino == "0-5":
            return round((nota_origen / 10) * 5, 1)
        
        # Convertir desde escala 0-100 a escala 0-5
        if escala_origen == "0-100" and escala_destino == "0-5":
            return round((nota_origen / 100) * 5, 1)
        
        # Convertir desde escala A-F a escala 0-5
        if escala_origen == "A-F" and escala_destino == "0-5":
            # Mapeo básico de letras a valores en escala 0-5
            conversion = {
                "A+": 5.0, "A": 4.8, "A-": 4.5,
                "B+": 4.2, "B": 4.0, "B-": 3.8,
                "C+": 3.5, "C": 3.3, "C-": 3.0,
                "D+": 2.8, "D": 2.5, "D-": 2.0,
                "F": 0.0
            }
            
            return conversion.get(nota_origen, 0.0)
        
        # Implementar más conversiones según sea necesario
        
        # Si no se conoce la conversión, devolver la nota original
        return nota_origen
    
    @staticmethod
    def get_promedio_intercambio(id_solicitud):
        """Calcula el promedio de las notas homologadas para una solicitud"""
        resultados = Resultado.get_by_solicitud(id_solicitud)
        
        if not resultados:
            return 0.0
        
        total_notas = 0
        suma_notas = 0
        
        for resultado in resultados:
            if resultado.get('estado_homologacion') == 'aprobada':
                total_notas += 1
                suma_notas += float(resultado.get('nota_convertida', 0))
        
        if total_notas == 0:
            return 0.0
        
        return round(suma_notas / total_notas, 2)