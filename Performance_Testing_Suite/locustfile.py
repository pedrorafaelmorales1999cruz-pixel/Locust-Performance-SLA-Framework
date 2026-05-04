# pyright: reportGeneralTypeIssues=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportCallIssue=false
# pyright: reportAttributeAccessIssue=false
from locust import task, between, events, FastHttpUser
import gevent
from config import Config
import logging
import random
import uuid
import csv
import os
import sys
import warnings

# Silenciar avisos de depuración de Locust (datetime) para una terminal limpia
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Colores ANSI para una terminal 
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    BLUE = '\033[94m'

def setup_folders():
    """Garantiza la existencia de directorios necesarios para reportes y logs."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    for folder_name in ["logs", "reports"]:
        folder_path = os.path.join(BASE_DIR, folder_name)
        if os.path.exists(folder_path) and not os.path.isdir(folder_path):
            os.rename(folder_path, folder_path + "_backup_file")
        os.makedirs(folder_path, exist_ok=True)

# Ejecutar preparación de entorno al importar el script
setup_folders()

# Evitar bloqueos de archivos en Windows al usar múltiples procesos (Master/Worker)
is_worker = "--worker" in sys.argv
log_file = Config.LOGS_PATH.replace(".log", f"_{os.getpid()}.log") if is_worker else Config.LOGS_PATH

logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

@events.init_command_line_parser.add_listener
def _(parser):
    """Añade argumentos personalizados a Locust para control de SLA dinámico."""
    parser.add_argument("--sla-p95", type=int, default=Config.SLA_P95_MS, help="SLA P95 en milisegundos")

class APIUser(FastHttpUser):
    """
    Define el comportamiento de los usuarios virtuales.
    Usamos FastHttpUser para maximizar el rendimiento en hardware limitado (Ryzen 3 / 8GB RAM).
    """
    wait_time = between(Config.MIN_WAIT, Config.MAX_WAIT)
    host = Config.BASE_URL
    
    # Carga de datos compartida a nivel de clase para ahorrar memoria
    user_data = [] 

    @classmethod
    def _load_csv_data(cls):
        """Carga thread-safe de datos compartidos."""
        try:
            with open(Config.DATA_PATH, mode='r', encoding='utf-8') as file:
                cls.user_data = list(csv.DictReader(file))
            logging.info(f"--- Datos CSV cargados: {len(cls.user_data)} registros ---")
        except Exception as e:
            logging.error(f"Error crítico cargando CSV: {e}")

    @task(3)
    def get_posts(self):
        """Simula usuarios consultando una lista de recursos."""
        try:
            with self.client.get("/posts", name="GET /posts", catch_response=True, timeout=Config.TIMEOUT) as response:
                if response.status_code == 200: # type: ignore
                    json_data = response.json()
                    # Validación técnica: Verificar que la respuesta sea una lista y no esté vacía
                    if isinstance(json_data, list) and len(json_data) > 0:
                        response.success()
                    else:
                        response.failure("Respuesta vacía o formato incorrecto")
                else:
                    response.failure(f"Status inesperado: {response.status_code}")
        except Exception as e:
            logging.error(f"Error de red detectado en GET /posts: {e}")

    @task(1)
    def get_single_post(self):
        """Simula la visualización de un detalle aleatorio para evitar falsos positivos por caché."""
        # Selección dinámica desde el CSV cargado
        post_id = random.choice(self.user_data)['id'] if self.user_data else random.randint(1, 10)
        
        try:
            with self.client.get(f"/posts/{post_id}", name="GET /posts/[id]", catch_response=True, timeout=Config.TIMEOUT) as response:
                if response.status_code == 200:
                    try:
                        json_res = response.json()
                        # Validación de integridad: Asegurar que el ID devuelto coincide (manejo de tipos string/int)
                        if json_res and str(json_res.get('id')) == str(post_id):
                            response.success()
                        elif json_res:
                            response.failure(f"ID devuelto ({json_res.get('id') if json_res else 'None'}) no coincide con solicitado ({post_id})")
                    except Exception:
                        response.failure("Error al parsear JSON de respuesta")
                else:
                    response.failure(f"Error {response.status_code} en post {post_id}")
        except Exception as e:
            logging.error(f"Error de red detectado en GET /posts/{post_id}: {e}")

    @task(1)
    def create_post(self):
        """Simula una operación de escritura (POST) a prueba de balas."""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "title": f"Post_QA_{unique_id}",
            "body": "Contenido generado en prueba de estrés",
            "userId": random.choice(self.user_data)['id'] if self.user_data else random.randint(1, 10)
        }
        try:
            with self.client.post("/posts", json=payload, name="POST /posts", catch_response=True, timeout=Config.TIMEOUT) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 0:
                    response.failure("Timeout: El servidor tardó más de 3 segundos.")
                else:
                    response.failure(f"Fallo en creación. Recibido HTTP: {response.status_code}")
        except Exception as e:
            logging.error(f"Caída de red detectada al crear post: {e}")

def print_realtime_stats(environment):
    """Tarea en segundo plano para imprimir métricas en tiempo real en la terminal."""
    while not environment.runner.state in ["stopped", "stopping"]:
        stats = environment.stats.total
        if stats.num_requests > 0:
            p95 = stats.get_response_time_percentile(0.95)
            rps = stats.total_rps
            fail_ratio = stats.fail_ratio * 100 # type: ignore
            color_p95 = Color.YELLOW if p95 > Config.SLA_P95_MS else Color.GREEN
            color_error = Color.RED if fail_ratio > 1 else Color.CYAN
            
            print(f"{Color.BOLD}{Color.BLUE}[MONITOR]{Color.RESET} "
                  f"Reqs: {Color.BOLD}{stats.num_requests}{Color.RESET} | "
                  f"RPS: {Color.GREEN}{rps:.1f}{Color.RESET} | "
                  f"P95: {color_p95}{p95:.0f}ms{Color.RESET} | "
                  f"Errores: {color_error}{fail_ratio:.1f}%{Color.RESET}")
        gevent.sleep(Config.STATS_REPORT_INTERVAL)

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Carga los datos iniciales una sola vez al arrancar Locust."""
    APIUser._load_csv_data()

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logging.info(f"--- Iniciando prueba de carga en: {environment.host} ---")
    if environment.runner:
        gevent.spawn(print_realtime_stats, environment)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print(f"\n{Color.BOLD}{Color.BLUE}┏" + "━"*58 + "┓")
    print(f"│{Color.CYAN}   📊 RESUMEN EJECUTIVO DE RENDIMIENTO" + " "*21 + f"{Color.BLUE}│")
    print(f"┗" + "━"*58 + f"┛{Color.RESET}")

    # Verificación de calidad: P95 y Tasa de Errores
    stats = environment.stats.total
    p95 = stats.get_response_time_percentile(0.95)
    fail_ratio = stats.fail_ratio
    
    # Usar el SLA definido por comando o por configuración
    sla_limit = environment.parsed_options.sla_p95 if hasattr(environment, 'parsed_options') else Config.SLA_P95_MS

    print(f"{Color.BOLD}➤ Métricas Clave:{Color.RESET}")
    color_p95 = Color.RED if p95 > sla_limit else Color.GREEN
    color_fails = Color.RED if fail_ratio > 0.01 else Color.GREEN
    
    print(f"   • Latencia P95:  {Color.BOLD}{color_p95}{p95:.2f}ms{Color.RESET} (Objetivo: <{sla_limit}ms)")
    print(f"   • Tasa Fallos:   {Color.BOLD}{color_fails}{fail_ratio*100:.2f}%{Color.RESET}")
    print(f"   • Total Reqs:    {Color.BOLD}{stats.num_requests}{Color.RESET}")

    success = True
    if p95 > sla_limit:
        print(f"\n{Color.YELLOW}{Color.BOLD} ⚠️  ALERTA SLA:{Color.RESET} La latencia superó el límite establecido.")
        success = False
    
    if fail_ratio > 0.01:
        print(f"{Color.RED}{Color.BOLD} ❌ ALERTA CALIDAD:{Color.RESET} La tasa de error es superior al 1%.")
        success = False

    if success:
        print(f"\n{Color.GREEN}{Color.BOLD} 🎉 RESULTADO: ¡PRUEBA EXITOSA!{Color.RESET}")
    else:
        print(f"\n{Color.RED}{Color.BOLD} 🚫 RESULTADO: PRUEBA FALLIDA (No cumple estándares){Color.RESET}")
    print(f"{Color.BLUE}" + "─"*60 + f"\n{Color.RESET}")