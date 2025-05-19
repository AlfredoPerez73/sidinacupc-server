from bson import ObjectId
from db.db import mongo
from datetime import datetime

class Docente:
    @staticmethod
    def create(data):
        """Crea un nuevo docente en la base de datos"""
        docente = {
            'nombre_completo': data.get('nombre_completo'),
            'documento_identidad': data.get('documento_identidad'),
            'tipo_documento': data.get('tipo_documento'),
            'email': data.get('email'),
            'telefono': data.get('telefono'),
            'fecha_nacimiento': data.get('fecha_nacimiento'),
            'direccion': data.get('direccion'),
            
            # Información académica
            'titulo_pregrado': data.get('titulo_pregrado'),
            'titulo_posgrado': data.get('titulo_posgrado'),
            'nivel_formacion': data.get('nivel_formacion'),  # Pregrado, Especialización, Maestría, Doctorado
            'departamento': data.get('departamento'),
            'facultad': data.get('facultad'),
            'categoria_docente': data.get('categoria_docente'),  # Titular, Asociado, Asistente, Instructor
            'tipo_vinculacion': data.get('tipo_vinculacion'),  # Planta, Cátedra, Ocasional
            
            # Información profesional
            'anos_experiencia': data.get('anos_experiencia'),
            'anos_experiencia_institucion': data.get('anos_experiencia_institucion'),
            'escalafon': data.get('escalafon'),
            'idiomas': data.get('idiomas', []),  # Lista de idiomas con nivel de competencia
            'areas_conocimiento': data.get('areas_conocimiento', []),
            
            # Producción académica
            'publicaciones': data.get('publicaciones', 0),
            'proyectos_investigacion': data.get('proyectos_investigacion', 0),
            'participacion_grupos_investigacion': data.get('participacion_grupos_investigacion', []),
            
            # Estado administrativo
            'estado': data.get('estado', 'activo'),
            'sanciones_academicas': data.get('sanciones_academicas', False),
            'sanciones_disciplinarias': data.get('sanciones_disciplinarias', False),
            'evaluacion_docente_promedio': data.get('evaluacion_docente_promedio'),  # Último promedio de evaluación
            
            # Experiencia internacional
            'experiencia_internacional': data.get('experiencia_internacional', False),
            'intercambios_previos': data.get('intercambios_previos', []),
            'redes_internacionales': data.get('redes_internacionales', []),
            
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = mongo.db.docentes.insert_one(docente)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(id_docente):
        """Obtiene un docente por su ID"""
        return mongo.db.docentes.find_one({'_id': ObjectId(id_docente)})
    
    @staticmethod
    def get_by_documento(documento):
        """Obtiene un docente por su número de documento"""
        return mongo.db.docentes.find_one({'documento_identidad': documento})
    
    @staticmethod
    def update(id_docente, data):
        """Actualiza los datos de un docente"""
        data['fecha_actualizacion'] = datetime.utcnow()
        
        mongo.db.docentes.update_one(
            {'_id': ObjectId(id_docente)},
            {'$set': data}
        )
        
        return Docente.get_by_id(id_docente)
    
    @staticmethod
    def delete(id_docente):
        """Elimina un docente (cambio de estado a inactivo)"""
        mongo.db.docentes.update_one(
            {'_id': ObjectId(id_docente)},
            {'$set': {'estado': 'inactivo', 'fecha_actualizacion': datetime.utcnow()}}
        )
        
        return True
    
    @staticmethod
    def get_all(filters=None, page=1, per_page=10):
        """Obtiene una lista paginada de docentes"""
        if filters is None:
            filters = {}
            
        skip = (page - 1) * per_page
        
        docentes = list(mongo.db.docentes.find(filters)
                       .sort('nombre_completo', 1)
                       .skip(skip)
                       .limit(per_page))
        
        total = mongo.db.docentes.count_documents(filters)
        
        return {
            'docentes': docentes,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def get_by_departamento(departamento):
        """Obtiene docentes por departamento"""
        return list(mongo.db.docentes.find({
            'departamento': departamento,
            'estado': 'activo'
        }))
    
    @staticmethod
    def get_by_categoria(categoria):
        """Obtiene docentes por categoría"""
        return list(mongo.db.docentes.find({
            'categoria_docente': categoria,
            'estado': 'activo'
        }))
    
    @staticmethod
    def cumple_requisitos_intercambio(id_docente):
        """Verifica si un docente cumple con los requisitos para intercambio"""
        docente = Docente.get_by_id(id_docente)
        
        if not docente:
            return False, "Docente no encontrado"
        
        # Verificar que sea docente de tiempo completo o medio tiempo
        if docente.get('tipo_vinculacion') not in ['Planta', 'Ocasional']:
            return False, "Debe ser docente de planta o ocasional de tiempo completo"
        
        # Verificar experiencia mínima en la institución (generalmente 2 años)
        if docente.get('anos_experiencia_institucion', 0) < 2:
            return False, "No cumple con la experiencia mínima en la institución"
        
        # Verificar nivel de formación mínimo (maestría para pregrado, doctorado para posgrado)
        nivel_formacion = docente.get('nivel_formacion', '')
        if nivel_formacion not in ['Maestría', 'Doctorado']:
            return False, "Nivel de formación insuficiente (se requiere mínimo maestría)"
        
        # Verificar evaluación docente (mínimo 4.0/5.0)
        evaluacion = docente.get('evaluacion_docente_promedio', 0)
        if evaluacion < 4.0:
            return False, "Evaluación docente insuficiente (mínimo 4.0)"
        
        # Verificar que no tenga sanciones académicas o disciplinarias
        if docente.get('sanciones_academicas', False):
            return False, "Tiene sanciones académicas vigentes"
        
        if docente.get('sanciones_disciplinarias', False):
            return False, "Tiene sanciones disciplinarias vigentes"
        
        # Verificar producción académica mínima
        publicaciones = docente.get('publicaciones', 0)
        proyectos = docente.get('proyectos_investigacion', 0)
        
        if publicaciones < 1 and proyectos < 1:
            return False, "No cuenta con producción académica mínima requerida"
        
        return True, "Cumple con todos los requisitos"
    
    @staticmethod
    def get_docentes_elegibles_intercambio():
        """Obtiene lista de docentes elegibles para intercambio"""
        # Pipeline de agregación para filtrar docentes elegibles
        pipeline = [
            {
                '$match': {
                    'estado': 'activo',
                    'tipo_vinculacion': {'$in': ['Planta', 'Ocasional']},
                    'anos_experiencia_institucion': {'$gte': 2},
                    'nivel_formacion': {'$in': ['Maestría', 'Doctorado']},
                    'evaluacion_docente_promedio': {'$gte': 4.0},
                    'sanciones_academicas': False,
                    'sanciones_disciplinarias': False,
                    '$or': [
                        {'publicaciones': {'$gte': 1}},
                        {'proyectos_investigacion': {'$gte': 1}}
                    ]
                }
            },
            {
                '$sort': {'nombre_completo': 1}
            }
        ]
        
        return list(mongo.db.docentes.aggregate(pipeline))
    
    @staticmethod
    def actualizar_experiencia_internacional(id_docente, experiencia_data):
        """Actualiza la experiencia internacional del docente"""
        docente = Docente.get_by_id(id_docente)
        if not docente:
            return False
        
        # Agregar nueva experiencia a la lista
        intercambios_previos = docente.get('intercambios_previos', [])
        intercambios_previos.append({
            'institucion': experiencia_data.get('institucion'),
            'pais': experiencia_data.get('pais'),
            'tipo_intercambio': experiencia_data.get('tipo_intercambio'),
            'fecha_inicio': experiencia_data.get('fecha_inicio'),
            'fecha_fin': experiencia_data.get('fecha_fin'),
            'actividades': experiencia_data.get('actividades'),
            'fecha_registro': datetime.utcnow()
        })
        
        # Actualizar el registro
        mongo.db.docentes.update_one(
            {'_id': ObjectId(id_docente)},
            {
                '$set': {
                    'intercambios_previos': intercambios_previos,
                    'experiencia_internacional': True,
                    'fecha_actualizacion': datetime.utcnow()
                }
            }
        )
        
        return True