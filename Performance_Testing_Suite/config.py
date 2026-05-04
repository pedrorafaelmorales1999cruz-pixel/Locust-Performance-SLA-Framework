import os

class Config:
    """Configuración centralizada para las pruebas de carga."""
    # URL por defecto (puedes usar JSONPlaceholder para pruebas seguras)
    BASE_URL = os.getenv("LOCUST_BASE_URL", "https://jsonplaceholder.typicode.com")
    
    # Tiempos de espera del usuario (en segundos)
    MIN_WAIT = 2.0
    MAX_WAIT = 5.0
    TIMEOUT = 3.0
    SLA_P95_MS = 1000  # Ajustado para mayor tolerancia bajo carga de 100 usuarios
    STATS_REPORT_INTERVAL = 10  # Segundos entre cada reporte en consola
    
    # Rutas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "users.csv")
    LOGS_PATH = os.path.join(BASE_DIR, "logs", "performance.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")