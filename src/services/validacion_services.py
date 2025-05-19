from models.estudiante import Estudiante
from models.solicitud import Solicitud
from models.asignatura import Asignatura
from models.resultado import Resultado
from db.db import mongo
from bson import ObjectId

class ValidacionService:
    @staticmethod
    def validar_requisitos_estudiante(id_estudiante):
        """Valida si un estudiante cumple con los requisitos para intercambio"""
        return Estudiante.cumple_requisitos_intercambio(id_estudiante)
    
    @staticmethod
    def validar_asignaturas_solicitud(id_solicitud):
        """Valida que las asignaturas de una solicitud cumplan con los requisitos mínimos"""
        # Obtener todas las asignaturas de la solicitud
        asignaturas = Asignatura.get_by_solicitud(id_solicitud)
        
        # Verificar si hay asignaturas
        if not asignaturas:
            return False, "No hay asignaturas registradas para esta solicitud"
        
        # Verificar el mínimo de créditos (según el artículo quinto del acuerdo)
        total_creditos = 0
        for asignatura in asignaturas:
            total_creditos += asignatura.get('creditos_asignatura_origen', 0)
        
        # El número mínimo es 6 créditos para pregrado (podría cambiar según reglamento)
        if total_creditos < 6:
            return False, f"El total de créditos ({total_creditos}) es menor al mínimo requerido (6)"
        
        # Verificar que las asignaturas tengan los campos requeridos
        for asignatura in asignaturas:
            if not asignatura.get('codigo_asignatura_origen'):
                return False, "Una o más asignaturas no tienen código de origen"
            if not asignatura.get('nombre_asignatura_origen'):
                return False, "Una o más asignaturas no tienen nombre de origen"
            if not asignatura.get('codigo_asignatura_destino'):
                return False, "Una o más asignaturas no tienen código de destino"
            if not asignatura.get('nombre_asignatura_destino'):
                return False, "Una o más asignaturas no tienen nombre de destino"
        
        return True, f"Las asignaturas cumplen con los requisitos mínimos. Total de créditos: {total_creditos}"
    
    @staticmethod
    def validar_proceso_aprobacion(id_solicitud, nivel_aprobacion):
        """Valida si una solicitud puede avanzar al siguiente nivel de aprobación"""
        solicitud = Solicitud.get_by_id(id_solicitud)
        
        if not solicitud:
            return False, "Solicitud no encontrada"
        
        if nivel_aprobacion == 'jefe_programa':
            # No hay requisitos previos para este nivel
            return True, "La solicitud puede ser evaluada por el jefe de programa"
        
        elif nivel_aprobacion == 'consejo_facultad':
            # Requiere aprobación del jefe de programa
            if not solicitud.get('jefe_programa_aprobacion'):
                return False, "La solicitud aún no ha sido aprobada por el jefe de programa"
            return True, "La solicitud puede ser evaluada por el consejo de facultad"
        
        elif nivel_aprobacion == 'orpi':
            # Requiere aprobación del consejo de facultad
            if not solicitud.get('consejo_facultad_aprobacion'):
                return False, "La solicitud aún no ha sido aprobada por el consejo de facultad"
            return True, "La solicitud puede ser evaluada por la oficina de ORPI"
        
        else:
            return False, "Nivel de aprobación no válido"
    
    @staticmethod
    def validar_homologacion_resultados(id_solicitud):
        """Valida si los resultados de una solicitud pueden ser homologados"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return False, "Solicitud no encontrada"
        
        # Verificar que la solicitud esté en estado adecuado
        if solicitud.get('estado_solicitud') != 'aprobada':
            return False, "La solicitud debe estar aprobada para homologar resultados"
        
        # Verificar que haya asignaturas registradas
        asignaturas = Asignatura.get_by_solicitud(id_solicitud)
        if not asignaturas:
            return False, "No hay asignaturas registradas para esta solicitud"
        
        # Verificar que haya resultados registrados para todas las asignaturas
        for asignatura in asignaturas:
            resultado = Resultado.get_by_asignatura(str(asignatura['_id']))
            if not resultado:
                return False, f"Falta registrar el resultado para la asignatura {asignatura.get('nombre_asignatura_origen')}"
        
        return True, "Los resultados pueden ser homologados"
    
    @staticmethod
    def validar_finalizacion_intercambio(id_solicitud):
        """Valida si un intercambio puede ser finalizado"""
        # Verificar si existe la solicitud
        solicitud = Solicitud.get_by_id(id_solicitud)
        if not solicitud:
            return False, "Solicitud no encontrada"
        
        # Verificar que la solicitud esté aprobada
        if solicitud.get('estado_solicitud') != 'aprobada':
            return False, "La solicitud debe estar aprobada para finalizar el intercambio"
        
        # Verificar que todos los resultados estén homologados
        todos_homologados = Resultado.verificar_todos_homologados(id_solicitud)
        if not todos_homologados:
            return False, "No todos los resultados han sido homologados"
        
        # Verificar que el seguimiento esté en estado adecuado
        seguimiento = seguimiento.get_by_solicitud(id_solicitud)
        if not seguimiento:
            return False, "No hay seguimiento registrado para esta solicitud"
        
        if seguimiento.get('estado_actual') != 'en proceso':
            return False, "El seguimiento debe estar en proceso para finalizar el intercambio"
        
        return True, "El intercambio puede ser finalizado"