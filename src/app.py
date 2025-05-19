from flask import Flask
from flask_cors import CORS
from config import Config
from db.db import initialize_db
from routes.auth_routes import auth_bp
from routes.estudiante_routes import estudiantes_bp
from routes.convenio_routes import convenios_bp
from routes.solicitud_routes import solicitudes_bp
from routes.asignatura_routes import asignaturas_bp
from routes.docente_routes import docente_bp
from routes.seguimiento_routes import seguimiento_bp
from routes.resultado_routes import resultados_bp
from routes.reportes_routes import reportes_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5000", "http://localhost:5173"],  # Ajusta según tus puertos
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True  # Esto es importante para credenciales
        }
    })
    
    # Inicializar la base de datos
    initialize_db(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(estudiantes_bp, url_prefix='/api/estudiantes')
    app.register_blueprint(docente_bp, url_prefix='/api/docentes')
    app.register_blueprint(convenios_bp, url_prefix='/api/convenios')
    app.register_blueprint(solicitudes_bp, url_prefix='/api/solicitudes')
    app.register_blueprint(asignaturas_bp, url_prefix='/api/asignaturas')
    app.register_blueprint(seguimiento_bp, url_prefix='/api/seguimiento')
    app.register_blueprint(resultados_bp, url_prefix='/api/resultados')
    app.register_blueprint(reportes_bp, url_prefix='/api/reportes')
    
    @app.route('/')
    def index():
        return {'message': 'API del Sistema de Información para la División de Internacionalización'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)