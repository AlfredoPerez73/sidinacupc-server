import re
from datetime import datetime
from bson.objectid import ObjectId

class Validators:
    @staticmethod
    def validate_email(email):
        """Valida que el email tenga un formato válido"""
        if not email:
            return False, "El email es requerido"
        
        # Patrón básico para validar email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "El formato del email no es válido"
        
        return True, "Email válido"
    
    @staticmethod
    def validate_documento(documento, tipo_documento):
        """Valida que el documento tenga un formato válido según su tipo"""
        if not documento:
            return False, "El documento es requerido"
        
        if tipo_documento == "CC":
            # Cédula de ciudadanía: solo números, longitud entre 8 y 10 dígitos
            if not documento.isdigit() or len(documento) < 8 or len(documento) > 10:
                return False, "La cédula debe contener entre 8 y 10 dígitos numéricos"
        
        elif tipo_documento == "TI":
            # Tarjeta de identidad: solo números, longitud entre 10 y 11 dígitos
            if not documento.isdigit() or len(documento) < 10 or len(documento) > 11:
                return False, "La tarjeta de identidad debe contener entre 10 y 11 dígitos numéricos"
        
        elif tipo_documento == "CE":
            # Cédula de extranjería: alfanumérico, longitud máxima 12 caracteres
            if len(documento) > 12:
                return False, "La cédula de extranjería debe contener máximo 12 caracteres"
        
        elif tipo_documento == "PAS":
            # Pasaporte: alfanumérico, longitud entre 6 y 15 caracteres
            if len(documento) < 6 or len(documento) > 15:
                return False, "El pasaporte debe contener entre 6 y 15 caracteres"
        
        return True, "Documento válido"
    
    @staticmethod
    def validate_object_id(id_str):
        """Valida que el ID tenga un formato válido de ObjectId de MongoDB"""
        if not id_str:
            return False, "El ID es requerido"
        
        try:
            ObjectId(id_str)
            return True, "ID válido"
        except:
            return False, "El formato del ID no es válido"
    
    @staticmethod
    def validate_nombre(nombre):
        """Valida que el nombre tenga un formato válido"""
        if not nombre:
            return False, "El nombre es requerido"
        
        if len(nombre) < 3:
            return False, "El nombre debe tener al menos 3 caracteres"
        
        # Verificar que no contenga caracteres especiales excepto espacios y guiones
        pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]+$'
        if not re.match(pattern, nombre):
            return False, "El nombre solo debe contener letras, espacios y guiones"
        
        return True, "Nombre válido"
    
    @staticmethod
    def validate_fecha(fecha_str, formato='%Y-%m-%d'):
        """Valida que la fecha tenga un formato válido"""
        if not fecha_str:
            return False, "La fecha es requerida"
        
        try:
            fecha = datetime.strptime(fecha_str, formato)
            return True, "Fecha válida"
        except ValueError:
            return False, f"El formato de fecha debe ser {formato}"
    
    @staticmethod
    def validate_periodo_academico(periodo):
        """Valida que el periodo académico tenga un formato válido (YYYY-P)"""
        if not periodo:
            return False, "El periodo académico es requerido"
        
        # Formato esperado: YYYY-P donde P es 1 o 2
        pattern = r'^[0-9]{4}-[1-2]$'
        if not re.match(pattern, periodo):
            return False, "El formato del periodo académico debe ser YYYY-P (P=1,2)"
        
        return True, "Periodo académico válido"
    
    @staticmethod
    def validate_promedio(promedio):
        """Valida que el promedio tenga un valor válido (entre 0 y 5)"""
        if promedio is None:
            return False, "El promedio es requerido"
        
        try:
            promedio_float = float(promedio)
            if promedio_float < 0 or promedio_float > 5:
                return False, "El promedio debe estar entre 0 y 5"
            
            return True, "Promedio válido"
        except ValueError:
            return False, "El promedio debe ser un número"
    
    @staticmethod
    def validate_creditos(creditos):
        """Valida que los créditos tengan un valor válido (entero positivo)"""
        if creditos is None:
            return False, "Los créditos son requeridos"
        
        try:
            creditos_int = int(creditos)
            if creditos_int <= 0:
                return False, "Los créditos deben ser un número entero positivo"
            
            return True, "Créditos válidos"
        except ValueError:
            return False, "Los créditos deben ser un número entero"
    
    @staticmethod
    def validate_tipo_intercambio(tipo):
        """Valida que el tipo de intercambio sea válido (nacional o internacional)"""
        if not tipo:
            return False, "El tipo de intercambio es requerido"
        
        tipos_validos = ['nacional', 'internacional']
        if tipo.lower() not in tipos_validos:
            return False, f"El tipo de intercambio debe ser uno de: {', '.join(tipos_validos)}"
        
        return True, "Tipo de intercambio válido"
    
    @staticmethod
    def validate_modalidad(modalidad):
        """Valida que la modalidad sea válida (presencial o virtual)"""
        if not modalidad:
            return False, "La modalidad es requerida"
        
        modalidades_validas = ['presencial', 'virtual']
        if modalidad.lower() not in modalidades_validas:
            return False, f"La modalidad debe ser una de: {', '.join(modalidades_validas)}"
        
        return True, "Modalidad válida"
    
    @staticmethod
    def validate_duracion(duracion):
        """Valida que la duración sea válida (1 o 2 periodos)"""
        if duracion is None:
            return False, "La duración es requerida"
        
        try:
            duracion_int = int(duracion)
            if duracion_int not in [1, 2]:
                return False, "La duración debe ser 1 o 2 periodos"
            
            return True, "Duración válida"
        except ValueError:
            return False, "La duración debe ser un número entero"
    
    @staticmethod
    def validate_estado_solicitud(estado):
        """Valida que el estado de la solicitud sea válido"""
        if not estado:
            return False, "El estado es requerido"
        
        estados_validos = ['pendiente', 'en revision', 'aprobada', 'rechazada', 'finalizada']
        if estado.lower() not in estados_validos:
            return False, f"El estado debe ser uno de: {', '.join(estados_validos)}"
        
        return True, "Estado válido"
    
    @staticmethod
    def validate_estado_seguimiento(estado):
        """Valida que el estado del seguimiento sea válido"""
        if not estado:
            return False, "El estado es requerido"
        
        estados_validos = ['pendiente', 'en proceso', 'finalizado', 'cancelado']
        if estado.lower() not in estados_validos:
            return False, f"El estado debe ser uno de: {', '.join(estados_validos)}"
        
        return True, "Estado válido"
    
    @staticmethod
    def validate_estado_homologacion(estado):
        """Valida que el estado de homologación sea válido"""
        if not estado:
            return False, "El estado es requerido"
        
        estados_validos = ['pendiente', 'aprobada', 'rechazada']
        if estado.lower() not in estados_validos:
            return False, f"El estado debe ser uno de: {', '.join(estados_validos)}"
        
        return True, "Estado válido"
    
    @staticmethod
    def validate_password(password):
        """Valida que la contraseña cumpla con los requisitos mínimos de seguridad"""
        if not password:
            return False, "La contraseña es requerida"
        
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        # Verificar que contenga al menos un número
        if not re.search(r'[0-9]', password):
            return False, "La contraseña debe contener al menos un número"
        
        # Verificar que contenga al menos una letra mayúscula
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una letra mayúscula"
        
        # Verificar que contenga al menos una letra minúscula
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una letra minúscula"
        
        # Verificar que contenga al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "La contraseña debe contener al menos un carácter especial"
        
        return True, "Contraseña válida"
    
    @staticmethod
    def validate_rol(rol):
        """Valida que el rol sea válido"""
        if not rol:
            return False, "El rol es requerido"
        
        roles_validos = ['admin', 'coordinador', 'jefe_programa', 'decano', 'estudiante', 'orpi']
        if rol.lower() not in roles_validos:
            return False, f"El rol debe ser uno de: {', '.join(roles_validos)}"
        
        return True, "Rol válido"
    
    @staticmethod
    def validate_calificacion(calificacion, escala='0-5'):
        """Valida que la calificación sea válida según la escala"""
        if calificacion is None:
            return False, "La calificación es requerida"
        
        if escala == '0-5':
            try:
                cal_float = float(calificacion)
                if cal_float < 0 or cal_float > 5:
                    return False, "La calificación debe estar entre 0 y 5"
                return True, "Calificación válida"
            except ValueError:
                return False, "La calificación debe ser un número"
                
        elif escala == '0-10':
            try:
                cal_float = float(calificacion)
                if cal_float < 0 or cal_float > 10:
                    return False, "La calificación debe estar entre 0 y 10"
                return True, "Calificación válida"
            except ValueError:
                return False, "La calificación debe ser un número"
                
        elif escala == '0-100':
            try:
                cal_float = float(calificacion)
                if cal_float < 0 or cal_float > 100:
                    return False, "La calificación debe estar entre 0 y 100"
                return True, "Calificación válida"
            except ValueError:
                return False, "La calificación debe ser un número"
                
        elif escala == 'A-F':
            # Verificar que sea una calificación válida en escala de letras
            calificaciones_validas = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']
            if calificacion not in calificaciones_validas:
                return False, f"La calificación debe ser una de: {', '.join(calificaciones_validas)}"
            return True, "Calificación válida"
            
        else:
            return False, f"Escala no soportada: {escala}"