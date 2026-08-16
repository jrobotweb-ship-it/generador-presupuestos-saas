# Generador de Presupuestos SaaS - Plataforma de Construcción

Este es el proyecto del **Generador de Presupuestos SaaS** con integración de Inteligencia Artificial para el cálculo de cómputos métricos en imágenes 3D, chat interactivo de ingeniería y redacción en lotes de memorias descriptivas técnicas extensas.

## 🔑 Credenciales de Acceso Administrador (Entorno de Desarrollo / Pruebas)

Para acceder al Panel de Control de Administración y gestionar usuarios, planes Pro, vigencias y sugerencias de soporte técnico, utiliza las siguientes credenciales en el modal de inicio de sesión:

*   **Email:** `admin@jrobotwweb.com` (o `admin@jrobotweb.com`)
*   **Contraseña:** `admin123`

*(Nota: Los correos configurados con permisos de administrador en el código son `admin@jrobotweb.com`, `admin@jrobotwweb.com`, `admin@presupuestos.jrobotweb.com` y `jrobotweb@gmail.com`)*

## 🚀 Cómo Iniciar el Servidor Local

1.  Asegúrate de tener instalado Python 3.10+.
2.  Haz doble clic en el archivo `iniciar_servidor.bat` (o ejecuta `python -m uvicorn main:app --port 8080` en tu terminal dentro de esta carpeta).
3.  Abre tu navegador de preferencia e ingresa a: **http://127.0.0.1:8080**

## 📂 Estructura del Proyecto

*   `main.py`: Servidor API y endpoints SaaS de autenticación, presupuestos, suscripción y administración.
*   `database.py` / `partidas.db`: Motor de base de datos SQLite y el catálogo completo comercial de **más de 1800 partidas**.
*   `memoria_ai.py` / `vision_ai.py` / `chat_ai.py`: Módulos de Inteligencia Artificial utilizando el modelo `gemini-2.5-flash`.
*   `pdf_generator.py` / `pdf_apu.py` / `pdf_memoria.py`: Módulos para generar reportes en formato PDF altamente personalizados con logotipos y firmas de empresa sin requerimiento de CIV.
*   `static/`: Archivos HTML, JS y CSS del frontend de control.
