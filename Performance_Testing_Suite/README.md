# 🚀 Locust Performance & SLA Framework

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Locust](https://img.shields.io/badge/Locust-76D7C4?style=for-the-badge&logo=locust&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

## 🎯 ¿Qué es este proyecto?
Esta es una suite de pruebas de rendimiento de nivel industrial diseñada para estresar y validar la escalabilidad de APIs. En lugar de hacer pruebas manuales, utilizamos **Locust** para simular cientos de usuarios concurrentes con comportamientos realistas.

**El objetivo:** Encontrar el punto de quiebre del sistema y asegurar que la experiencia del usuario sea rápida, incluso bajo mucha presión.

## 🛠️ Requisitos
- Python 3.9+
- Entorno virtual (`.venv`) activado.

## 🚀 Instalación y Uso

1. **Preparar el entorno:**
   ```bash
   python -m venv .venv
   # En Windows:
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configurar datos de prueba:**
   Crea un archivo llamado `users.csv` en la raíz del proyecto con el siguiente formato:
   ```csv
   id,username
   1,test_user_1
   2,test_user_2
   ```

3. **Modo Visual (Interfaz Web):**
   Ideal para observar gráficas en tiempo real.
   ```bash
   cd Locust-Performance-SLA-Framework
   locust -f locustfile.py
   ```
   Luego abre: [http://localhost:8089](http://localhost:8089)

4. **Modo Profesional (Headless):**
   Ideal para servidores y CI/CD. Consume **muchos menos recursos** de tu CPU.
   ```bash
   cd Locust-Performance-SLA-Framework
   locust -f locustfile.py --headless -u 100 -r 10 --run-time 2m --host https://jsonplaceholder.typicode.com --html reports/performance_report.html --sla-p95 1000
   ```

## 💎 Pilares de Ingeniería de esta Suite

### 1. Control Dinámico via CLI
La suite permite inyectar el valor del SLA directamente desde la terminal con el parámetro `--sla-p95`, facilitando su integración en distintos entornos (QA, Staging, Prod) sin cambiar una sola línea de código.

### 2. Optimización de Recursos (FastHttpUser)
A diferencia del `HttpUser` estándar, utilizamos **FastHttpUser**. Esto permite que incluso en equipos con recursos limitados (ej. Ryzen 3 / 8GB RAM), podamos simular cientos de usuarios sin que el procesador sature las mediciones, garantizando resultados precisos.

### 3. Gestión de Datos Dinámicos (CSV & UUID)
No usamos datos fijos. El script lee IDs reales desde un archivo `users.csv` y genera UUIDs únicos para cada post. Esto evita que el servidor responda desde el "caché" y lo obliga a trabajar realmente con la base de datos.

### 4. Aseguramiento de Calidad Automatizado (SLA)
La prueba no solo termina; se autoevalúa. 
- **¿Qué es P95?** Significa que el 95% de tus usuarios tuvieron una experiencia rápida.
- Si el P95 supera los **1000ms**, el script lanza una alerta automática. Esto es vital para garantizar la calidad en contratos de servicios (SLAs).

### 5. Arquitectura Modular y Resiliente
- **`config.py`**: El cerebro. Todas las variables (URLs, timeouts, SLAs) se cambian aquí sin tocar el código.
- **Resiliencia**: Manejo de errores de red y timeouts integrados para que la prueba no se detenga ante un fallo puntual.
- **Logs Inteligentes**: Registro detallado en la carpeta `/logs` para auditoría post-morterm.

## 📂 Estructura del Proyecto
```text
Locust-Performance-SLA-Framework/
├── logs/               # Registros de errores y eventos
├── reports/            # Reportes HTML generados
├── locustfile.py       # Lógica de los usuarios virtuales
├── config.py           # Configuración global
└── users.csv           # Datos de entrada para inyección dinámica
```

## 📈 Cómo leer los resultados
Al finalizar, revisa el archivo en `reports/senior_report.html`.

| Métrica | ¿Qué significa? | Estado Ideal |
| :--- | :--- | :--- |
| **95%ile (P95)** | El tiempo que experimenta la mayoría. | **< 1000ms** |
| **RPS** | Peticiones por segundo (Velocidad). | **Constante** |
| **Failures** | Errores o caídas del sistema. | **0.0%** |

> 💡 **Tip para Principiantes:** Si ves que la gráfica de latencia sube como una montaña, el servidor se está cansando. Si ves líneas rojas, el servidor se ha caído.

---
*Desarrollado como una solución escalable para pruebas de carga continua.*

---
## 📩 Contacto
¡Hola! Soy **Pedro Rafael**, entusiasta del Software Testing y la Automatización. 

[!LinkedIn](https://www.linkedin.com/in/pedrorafael-morales)

- 🛠️ Especialidad: Pruebas manuales y automatización con Python/Selenium.
- 📍 Ubicación: Monterrey, Nuevo León.
