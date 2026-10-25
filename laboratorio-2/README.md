# Laboratorio 2: reembolsos con aprobación humana (human-in-the-loop)

Este laboratorio es un **caso resuelto** de la sesión 2: un equipo de agentes
analiza una solicitud de reembolso y propone una acción, pero solo una
**persona** puede autorizarla. La autorización ocurre dentro del grafo con una
**pausa real y reanudable**: `interrupt()`, un checkpointer (`InMemorySaver`) y
`Command(resume=...)` con el mismo `thread_id`.

El notebook principal es:

[`02_Reembolsos_HITL_Estudiante.ipynb`](./02_Reembolsos_HITL_Estudiante.ipynb)

Consulta el [resumen de temas y puntos clave](./resumen.md) antes o después de
ejecutar el notebook. Todos los datos son ficticios y no se realiza ningún pago:
el "reembolso" es un registro en memoria.

## Preparar el entorno

Las dependencias están en [`requirements.txt`](./requirements.txt) y son las
mismas que las de los laboratorios 0 y 1, así que **puedes reutilizar el mismo
entorno virtual**. Un entorno virtual no es portable entre sistemas operativos:
si el repositorio está en una carpeta sincronizada (por ejemplo OneDrive) y lo
usas en Windows y macOS, crea un entorno distinto en cada sistema.

### Windows (PowerShell, en la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r laboratorio-2/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

### macOS / Linux (terminal, en la raíz del repositorio)

```bash
python3 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install -r laboratorio-2/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

Se recomienda Python 3.13 (probado también con 3.12).

## Configurar Groq

Solo hace falta para el modo real (`MODO_SIMULADO = False`). El archivo `.env`
debe estar en la raíz del repositorio; puedes crearlo a partir de la plantilla
[`.env.example`](../.env.example):

```bash
cp .env.example .env
```

```text
GROQ_API_KEY=tu_clave_nueva
```

El notebook carga esta variable con `python-dotenv` y no imprime su valor. El
modelo puede cambiarse con la variable opcional `GROQ_MODEL` (por defecto
`openai/gpt-oss-120b`). Nunca escribas la clave en una celda ni la confirmes en
Git.

## Validar los requisitos antes de ejecutar

Con el entorno activo, desde la raíz del repositorio:

```bash
python laboratorio-2/validar_entorno.py            # comprobaciones locales
python laboratorio-2/validar_entorno.py --online   # además consulta Groq
```

El script no consume tokens y nunca imprime la clave. Comprueba la versión de
Python y el entorno virtual, los paquetes de `requirements.txt`, que LangGraph
incluya `interrupt`, `Command` e `InMemorySaver`, el kernel, el `.env`, que el
notebook sea válido y no contenga ninguna clave `gsk_…`, el valor de
`MODO_SIMULADO` y si `DECISION` ya viene escrita en el paso 8. Termina con
código 0 si no hay errores y con 1 si hay alguno.

## Ejecutar en VS Code

1. Abre el notebook desde esta carpeta.
2. Pulsa **Seleccionar kernel** en la esquina superior derecha.
3. Elige **Python (Multiagentica)** o el intérprete del entorno
   (`.venv\Scripts\python.exe` en Windows, `.venv-mac/bin/python` en macOS).
4. Reinicia el kernel.
5. Ejecuta las celdas **en orden, una por una**.

La guía pide evitar *Ejecutar todo*: el objetivo es **observar la pausa** del
paso 6 y leer el payload antes de decidir en el paso 8.

| Paso | Qué ocurre |
|---|---|
| 6 | El grafo corre hasta `interrupt()` y **se detiene**; la celda termina, pero el caso queda guardado en el checkpointer |
| 7 | Inspeccionas el checkpoint: campos escritos y nodo pendiente (`revision_humana`) |
| 8 | Escribes `DECISION`, `REVISOR` y `MOTIVO` y reanudas con `Command(resume=...)` |
| 9 | Compruebas que `revision_humana` se ejecutó **dos veces** (al pausar y al reanudar) |
| 10 | Nueve pruebas automáticas: espera, aprobación, idempotencia, rechazo, hilos, entrada inválida, plazo y guardrails |

`DECISION` debería empezar en `None` para que ningún caso se apruebe o rechace
sin leer el payload. Una solicitud se reanuda una sola vez: para probar la otra
decisión, vuelve al paso 6. Si reinicias el kernel, los casos pausados se
pierden, porque `InMemorySaver` vive en memoria.

## Modos de ejecución y costo

| Modo | `MODO_SIMULADO` | Llamadas a Groq |
|---|---|---|
| Simulado | `True` | Ninguna; respuestas fijas que también pasan por los contratos Pydantic |
| Real | `False` | Unas 19 por ejecución completa (ver tabla siguiente) |

| Parte del notebook | Llamadas en modo real |
|---|---|
| Agente aislado (paso 3.1) | 1 |
| Iniciar la solicitud (paso 6) | 3 (atención, políticas, supervisor) |
| Reanudar (paso 8) | 0: los nodos anteriores a la pausa no se repiten |
| Pruebas automáticas (paso 10) | 15 (5 solicitudes × 3 agentes) |

En modo real, si el modelo devuelve un JSON que no cumple el contrato, el flujo
se detiene con `ValidationError` **antes** de la autorización. Es el
comportamiento esperado: nunca se "arregla" la respuesta inventando datos.

> ⚠️ **Ejecuta las pruebas del paso 10 en modo simulado.** Están diseñadas
> para respuestas fijas: las pruebas 1 a 5 suponen que el supervisor recomienda
> `reembolsar` y que el grafo se pausa. Con Groq real la recomendación varía:
> como el defecto no tiene evidencia, a veces el modelo recomienda
> `solicitar_informacion`, el caso se cierra sin revisión humana y esas pruebas
> fallan ("no se pausó"). En una ejecución local con Groq pasaron 4 de 9; en
> modo simulado pasan las 9. No es un error del entorno: es la variabilidad del
> LLM, y la decisión de pedir información es razonable para este caso.

## Ejecutar en Google Colab

El notebook funciona en Colab sin cambios: si no encuentra `.env`, lee la clave
de los Secrets.

1. Sube el `.ipynb` a Colab (**Archivo → Subir notebook**).
2. Abre el panel 🔑 **Secrets**, crea `GROQ_API_KEY` con tu clave y activa
   **Acceso del notebook**.
3. Ejecuta las celdas en orden, una por una.

El diagrama del grafo (paso 5) se genera con un servicio externo y requiere
conexión a internet; si falla, el notebook imprime el código Mermaid.
