# Laboratorio 7: MCP y A2A con LangGraph, LangChain y Gradio

Este laboratorio es un **caso resuelto** que continúa la sucursal bancaria
ficticia de los laboratorios 5 y 6. En lugar de un solo programa con todos los
agentes dentro, el sistema se separa en piezas que se comunican con
**protocolos estándar**:

| Pieza | Qué es | Protocolo |
|---|---|---|
| 🧑‍💼 **Asesor** | Agente principal (LangChain + LangGraph + Groq). Habla con el cliente | — |
| 🗄️ **Servidor MCP "Core bancario"** | Expone **herramientas**: saldo y movimientos | **MCP** |
| 🤖 **Agente de Créditos** | **Otro agente**, con su propio LLM y su propia herramienta. Simula cuotas | **A2A** |

Incluye una interfaz en **Gradio** que dibuja en vivo un diagrama de secuencia
con el color del protocolo por el que viajó cada mensaje.

El notebook principal es:

[`07_MCP_A2A_LangGraph_Gradio.ipynb`](./07_MCP_A2A_LangGraph_Gradio.ipynb)

Consulta el [resumen de temas y puntos clave](./resumen.md) antes o después de
ejecutarlo. Todo es ficticio: clientes, saldos y tasas son inventados para la
clase, y el ejemplo no aprueba créditos.

La carpeta incluye además una **sesión adicional** con el ejercicio del final
del notebook resuelto:
[`07b_Ejercicio_Tasa_y_Requisitos.ipynb`](./07b_Ejercicio_Tasa_y_Requisitos.ipynb).
Se describe al final de este documento.

La carpeta [`ViajaFacil/`](./ViajaFacil/) resuelve la **Actividad ViajaFácil
v2**: el diseño (Parte A), el notebook del reto con sus 7 huecos completos y un
notebook propio con un flujo en paralelo (RAG, MCP y A2A simulados y aprobación
humana). Ver su [README](./ViajaFacil/README.md).

## Preparar el entorno

Las dependencias están en [`requirements.txt`](./requirements.txt). Son las del
laboratorio 5 **más LangChain y los SDK de los dos protocolos**: `mcp`
(servidor y cliente MCP), `langchain-mcp-adapters` (herramientas MCP como
herramientas de LangChain) y `a2a-sdk[http-server]` (servidor y cliente A2A).
No necesita los embeddings ni FAISS del laboratorio 6, así que la instalación es
ligera. Si reutilizas el entorno virtual debes volver a instalar los requisitos
de esta carpeta. Un entorno virtual no es portable entre sistemas operativos: si
usas el repositorio en Windows y macOS, crea un entorno distinto en cada
sistema.

### Windows (PowerShell, en la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r laboratorio-7/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

### macOS / Linux (terminal, en la raíz del repositorio)

```bash
python3 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install -r laboratorio-7/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

Se recomienda Python 3.13 (probado en Windows con Python 3.13.2, LangChain 1.4,
LangGraph 1.2, mcp 1.30, langchain-mcp-adapters 0.3, a2a-sdk 1.3 y
Gradio 6.31). Los SDK de MCP y A2A cambian rápido: el notebook usa la API de
`a2a-sdk` 1.x (`create_agent_card_routes`, `create_client`, roles
`ROLE_USER`/`ROLE_AGENT`), que no es compatible con la 0.x.

## Configurar Groq

Este notebook **no tiene modo simulado**: el Asesor y el Agente de Créditos usan
Groq, así que la clave es obligatoria. El archivo `.env` debe estar en la raíz
del repositorio; puedes crearlo a partir de la plantilla
[`.env.example`](../.env.example):

```bash
cp .env.example .env
```

```text
GROQ_API_KEY=tu_clave_nueva
```

El notebook carga esta variable con `python-dotenv` y no imprime su valor. El
modelo está fijo en `openai/gpt-oss-120b` (el notebook usa `reasoning_effort`,
que solo aceptan los modelos gpt-oss), así que `GROQ_MODEL` no se aplica aquí.
Nunca escribas la clave en una celda ni la confirmes en Git.

## Validar los requisitos antes de ejecutar

Con el entorno activo, desde la raíz del repositorio:

```bash
python laboratorio-7/validar_entorno.py            # comprobaciones locales
python laboratorio-7/validar_entorno.py --online   # además consulta Groq
```

El script no consume tokens y nunca imprime la clave. Comprueba la versión de
Python y el entorno virtual, los paquetes de `requirements.txt`, que los SDK
incluyan las piezas que usa el notebook (`create_agent`, `FastMCP`,
`MultiServerMCPClient`, las rutas y el cliente de `a2a-sdk` 1.x), el kernel, el
`.env`, que los puertos 8001, 9999, 9998 y 7860 estén libres, y que los dos
notebooks (el principal y el de la sesión adicional) sean válidos, lean la
clave de `.env`, no contengan ninguna clave `gsk_…` y no creen un enlace
público con `demo.launch()` fuera de Colab. Con `--online` comprueba
además Groq. Termina con código 0 si no hay errores y con 1 si hay alguno.

## Ejecutar en VS Code

1. Abre el notebook desde esta carpeta.
2. Pulsa **Seleccionar kernel** en la esquina superior derecha.
3. Elige **Python (Multiagentica)** o el intérprete del entorno
   (`.venv\Scripts\python.exe` en Windows, `.venv-mac/bin/python` en macOS).
4. Reinicia el kernel.
5. Ejecuta las celdas en orden, de los pasos 0 al 12.

| Paso | Qué ocurre |
|---|---|
| 0 | Instala solo lo que falte (en local, si ya instalaste `requirements.txt`, no descarga nada) y conecta con Groq: debe imprimir `conectado` |
| 1 | Crea la bitácora compartida |
| 2 | Define el servidor MCP con `consultar_saldo` y `listar_movimientos` |
| 3 | Arranca el servidor MCP en `http://127.0.0.1:8001/mcp` (en un hilo) |
| 4 | Habla con MCP «a mano»: `initialize`, `tools/list`, `tools/call` → `saldo_cop: 5000000` |
| 5 | Un agente de LangChain usa las herramientas MCP por su cuenta |
| 6 | Define el Agente de Créditos con su herramienta local `simular_cuota` |
| 7 | Lo publica como servidor A2A en `http://127.0.0.1:9999/` |
| 8 | Lee la Agent Card y le envía un `SendMessage` JSON-RPC «a mano» |
| 9 | Envuelve la llamada A2A como herramienta del Asesor |
| 10 | El Asesor responde la pregunta mixta (MCP + A2A) y muestra la bitácora |
| 11 | Abre la interfaz en `http://127.0.0.1:7860` (o el siguiente puerto libre) |
| 12 | Cierra el servidor de Gradio |

### Los servidores en segundo plano

El servidor MCP (puerto 8001) y el Agente de Créditos (puerto 9999) corren con
`uvicorn` en **hilos** dentro del mismo kernel, para que compartan la bitácora
con Gradio. En producción vivirían en otras máquinas.

- Si vuelves a ejecutar el paso 3 o el 7, el notebook ve el puerto ocupado y
  **no** arranca un servidor nuevo: sigue respondiendo el código anterior. Si
  cambias el código de un servidor, **reinicia el kernel** y ejecuta todo.
- Los hilos se detienen al reiniciar o cerrar el kernel; no hay una celda para
  apagarlos.
- Los servidores escuchan solo en `127.0.0.1`: no son accesibles desde otros
  equipos.

### La interfaz de Gradio en local

- En local la interfaz **no** crea un enlace público: solo es accesible desde tu
  equipo. En Colab sí se crea (`share=True`), porque es la única forma de
  abrirla desde allí.
- VS Code puede mostrarla dentro del notebook. Si no se ve, abre en el navegador
  la URL local que imprime el paso 11.
- La celda del paso 11 termina enseguida, pero el servidor sigue activo hasta
  que ejecutes el paso 12 o reinicies el kernel.
- Al importar Gradio puede aparecer `TqdmWarning: IProgress not found`. Es
  inofensivo.
- En Windows, al cerrar cada conexión HTTP, asyncio registra un
  `ConnectionResetError [WinError 10054]` inofensivo. El paso 1 oculta solo ese
  aviso; los demás errores se siguen mostrando.

## Costo en llamadas a Groq

Cada agente es un `create_agent` que llama al LLM al menos dos veces (decidir
la herramienta y redactar). Cuando el Asesor delega por A2A, el Agente de
Créditos hace sus propias llamadas.

| Parte | Llamadas aproximadas |
|---|---|
| Ejecución completa del notebook (pasos 0 a 10) | ~11 |
| Interfaz: «¿Cuánto saldo tengo?» (solo MCP) | ~2 |
| Interfaz: «Simula una moto…» (A2A) | ~4 |
| Interfaz: pregunta mixta (MCP + A2A) | ~4 |

Si recibes un error 429 (límite de peticiones), espera unos segundos y repite.
Las llamadas MCP y la simulación de la cuota no consumen tokens: las resuelve
Python (≈ **$498.215** para $15.000.000 a 36 meses al 1 %).

## Ejecutar en Google Colab

El notebook funciona en Colab sin cambios: si no encuentra `.env`, lee la clave
de los Secrets, no reinstala `gradio`, `pandas` ni `uvicorn`, y crea el enlace
público de la interfaz.

1. Sube el `.ipynb` a Colab (**Archivo → Subir notebook**).
2. Abre el panel 🔑 **Secrets**, crea `GROQ_API_KEY` con tu clave y activa
   **Acceso del notebook**.
3. Ejecuta las celdas en orden.

Si Colab muestra avisos rojos de dependencias de paquetes que el notebook no
usa (`google-adk`, etc.), puedes ignorarlos.

## Sesión adicional: el ejercicio resuelto

El notebook principal termina con un ejercicio de dos partes. La sesión
adicional lo resuelve en un notebook **autocontenido**, que vuelve a levantar
todas las piezas sin ejecutar antes el 07:

[`07b_Ejercicio_Tasa_y_Requisitos.ipynb`](./07b_Ejercicio_Tasa_y_Requisitos.ipynb)

| Parte del ejercicio | Qué se agrega | ¿Cambia el Asesor? |
|---|---|---|
| 1 · MCP | La herramienta `consultar_tasa()` en el servidor MCP (sin parámetros; devuelve el 1 % mensual) | **No**: la descubre con `tools/list` |
| 2 · A2A | Un **Agente de Requisitos** en el puerto `9998`, con su LLM y su herramienta local `verificar_requisitos` (límite = 35 % del ingreso − obligaciones, la regla del laboratorio 5) | Una herramienta más, `consultar_agente_requisitos` |

Además:

- El paso 7 del notebook 07 se convierte en una receta, `publicar_a2a(...)`,
  que publica a los dos agentes A2A. Solo cambian la Agent Card, la *skill*, el
  agente y el puerto; el ejecutor y las rutas son los mismos.
- `arrancar` distingue un puerto que abrió **este** kernel (re-ejecución) de
  uno ocupado por **otro** programa. En el segundo caso se detiene con un error
  claro en lugar de usar en silencio el servidor viejo, que no tiene
  `consultar_tasa`.
- La interfaz de Gradio tiene un quinto carril (📋 Agente Requisitos).
- Tras la pregunta de referencia, el paso 10 comprueba en la bitácora que el
  Asesor usó `consultar_tasa`, que delegó en los dos agentes y que la respuesta
  trae la cuota ($498.215) y el límite ($525.000).

Se prepara igual que el notebook principal: mismo entorno, mismo `.env` y los
pasos 0 a 12. Los puertos son 8001 (MCP), 9999 (Créditos), 9998 (Requisitos) y
7860 (Gradio).

> ⚠️ Si el notebook 07 sigue abierto, **reinicia o cierra su kernel** antes de
> ejecutar el 07b: sus servidores ocupan los puertos 8001 y 9999 y el paso 3
> del 07b se detendrá con `RuntimeError: El puerto 8001 está ocupado…`.

La pregunta de referencia («Gano 3.500.000 al mes y tengo obligaciones por
700.000. ¿Qué tasa manejan? Simula una moto… y dime si la cuota cabe en los
requisitos») cuesta unas **7 llamadas a Groq**: 3 del Asesor y 2 de cada agente
remoto. Una ejecución completa del notebook hace unas 10. El cierre propone
preguntas de discusión y tres retos opcionales: que el Agente de Créditos lea la
tasa por MCP, crear las herramientas A2A automáticamente a partir de las Agent
Cards y probar un caso en que la cuota no cabe.
