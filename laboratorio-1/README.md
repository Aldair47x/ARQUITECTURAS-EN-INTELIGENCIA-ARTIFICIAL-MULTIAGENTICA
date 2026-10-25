# Laboratorio 1: respuesta a incidentes de pagos multiagente

Este laboratorio es la **entrega 01**: parte del patrón de revisión editorial del
[laboratorio 0](../laboratorio-0/) y lo transforma en una arquitectura de
**respuesta a incidentes de pagos** con LangGraph. El sistema tiene cuatro
agentes LLM (operaciones, riesgos, auditoría y supervisor), una regla
determinista de escalamiento y un punto de revisión humana simulado.

El notebook principal es:

[`01_RETO_Estudiante_Arquitectura_Pagos.ipynb`](./01_RETO_Estudiante_Arquitectura_Pagos.ipynb)

Consulta el [resumen de temas y puntos clave](./resumen.md) antes o después de
ejecutar el notebook.

## Preparar el entorno

Las dependencias están en [`requirements.txt`](./requirements.txt) y son las
mismas que las del laboratorio 0, así que **puedes reutilizar el mismo entorno
virtual**. Un entorno virtual no es portable entre sistemas operativos: si el
repositorio está en una carpeta sincronizada (por ejemplo OneDrive) y lo usas en
Windows y macOS, crea un entorno distinto en cada sistema.

### Windows (PowerShell, en la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r laboratorio-1/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

### macOS / Linux (terminal, en la raíz del repositorio)

```bash
python3 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install -r laboratorio-1/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

Se recomienda Python 3.13 (probado también con 3.12). Python 3.15 puede
intentar compilar pandas desde código fuente si no existe una rueda compatible.

## Configurar Groq

El archivo `.env` debe estar en la raíz del repositorio. Puedes crearlo a partir
de la plantilla [`.env.example`](../.env.example):

```bash
cp .env.example .env
```

```text
GROQ_API_KEY=tu_clave_nueva
```

El notebook carga esta variable con `python-dotenv` y no imprime su valor.
Nunca escribas la clave directamente en una celda ni la incluyas en la entrega;
si una clave fue compartida públicamente, revócala y crea una nueva.

El modelo puede cambiarse con la variable opcional `GROQ_MODEL` en `.env`
(por defecto `openai/gpt-oss-120b`).

## Validar los requisitos antes de ejecutar

Con el entorno activo, desde la raíz del repositorio:

```bash
python laboratorio-1/validar_entorno.py            # comprobaciones locales
python laboratorio-1/validar_entorno.py --online   # además consulta Groq
```

El script no consume tokens y nunca imprime la clave. Comprueba:

| Comprobación | Qué verifica |
|---|---|
| Intérprete | Versión de Python y que estés dentro de un entorno virtual |
| Paquetes | Que cada dependencia de `requirements.txt` esté instalada, en rango e importable |
| Kernel | Que `ipykernel` esté disponible y, opcionalmente, el kernel `multiagentica` |
| Configuración | Que exista `.env`, que `GROQ_API_KEY` tenga un valor real y qué modelo se usará |
| Notebook | JSON válido, **ninguna clave `gsk_…` en el código ni en las salidas**, y cuántos TODO quedan pendientes |
| Conexión (`--online`) | Que Groq responda, que el modelo exista en tu cuenta y que `mermaid.ink` sea accesible |

Termina con código 0 si no hay errores (las advertencias no cuentan) y con 1 si
hay alguno. Ejecútalo también antes de entregar para confirmar que no quedó
ninguna clave en el notebook.

## Ejecutar en VS Code

1. Abre el notebook desde esta carpeta.
2. Pulsa **Seleccionar kernel** en la esquina superior derecha.
3. Elige **Python (Multiagentica)** o el intérprete del entorno
   (`.venv\Scripts\python.exe` en Windows, `.venv-mac/bin/python` en macOS).
4. Reinicia el kernel.
5. Ejecuta la celda de instalación (3.1) y luego las demás **en orden**.

## Ejecutar en Google Colab

El notebook también funciona en Colab sin cambios: si no encuentra `.env`, lee
la clave de los Secrets.

1. Sube el `.ipynb` a Colab (**Archivo → Subir notebook**).
2. Abre el panel 🔑 **Secrets**, crea `GROQ_API_KEY` con tu clave y activa
   **Acceso del notebook**.
3. Ejecuta **Entorno de ejecución → Ejecutar todas**. La celda 3.1 instala
   las dependencias; pandas no se fija a una versión concreta porque Colab ya
   lo incluye y forzar otra puede obligar a reiniciar el entorno.

Sin la clave, la celda 3.2 se detiene con el mensaje
`Configura GROQ_API_KEY en .env o en los Secrets de Colab.`

## Cómo trabajar el reto

Busca las celdas marcadas con **🛠️ TODO** (tareas 1 a 8). Tras cada una hay una
celda **🧪 Autocomprobación** que verifica la estructura de tu código con un LLM
falso, sin gastar tokens. No cambies los nombres de funciones ni variables
pedidas: las autocomprobaciones dependen de ellos.

Un orden de trabajo recomendado:

1. Responder la sección 1 y ejecutar la preparación (secciones 2 a 4).
2. Con `MODO_SIMULADO = True`, programar las tareas 1 a 6 hasta que todas las
   autocomprobaciones muestren 🎉.
3. Cambiar a `MODO_SIMULADO = False` y ejecutar el grafo con Groq (sección 10.1).
4. Ejecutar la tarea 7 (4 casos) y la tarea 8 (3 repeticiones por variante) con
   Groq real, y escribir el análisis de la sección 13.
5. Revisar el checklist final y ejecutar `validar_entorno.py`.

## Modos de ejecución y costo

| Modo | `MODO_SIMULADO` | Llamadas a Groq |
|---|---|---|
| Simulado | `True` | Ninguna; respuestas fijas para depurar el flujo |
| Real | `False` | Ver tabla siguiente |

| Parte del notebook | Llamadas en modo real |
|---|---|
| Baseline (tarea 1) | 1 |
| Ejecución del grafo (sección 10.1) | 4 |
| Casos de prueba (tarea 7) | 16 (4 casos × 4 agentes) |
| Experimento (tarea 8) | 15 (3 × (1 + 4)) |

Si recibes un error 413 o 429 (límite de tokens o peticiones por minuto), espera
un minuto y vuelve a ejecutar la celda; no la relances en bucle.

El diagrama del grafo (sección 10.1) se genera con un servicio externo y
requiere conexión a internet; si falla, el notebook imprime el código Mermaid.

## Entregables

Según el propio notebook, la entrega incluye:

- el notebook completado, ejecutado con Groq real y sin la clave;
- captura o código Mermaid del grafo;
- la tabla de casos de prueba con su análisis y el experimento comparativo;
- un **ADR de máximo 2 páginas** con diagrama, al menos dos alternativas y su
  justificación (se entrega por separado): [`adr.md`](./adr.md), exportado a
  [`ADR-001_Arquitectura_Pagos_Aldair_Bernal.pdf`](./ADR-001_Arquitectura_Pagos_Aldair_Bernal.pdf).
