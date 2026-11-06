#!/usr/bin/env python3
"""Valida que el entorno cumpla los requisitos para ejecutar el notebook del laboratorio 7.

Solo usa la biblioteca estándar, así que funciona aunque falten dependencias.
Nunca imprime el valor de la clave de Groq.

Uso (desde la raíz del repositorio, con el entorno virtual activado):

    python laboratorio-7/validar_entorno.py            # comprobaciones locales
    python laboratorio-7/validar_entorno.py --online   # además consulta Groq (sin consumir tokens)

Código de salida: 0 si no hay errores (las advertencias no cuentan), 1 si hay errores.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
from importlib import metadata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
NOTEBOOKS = [AQUI / "07_MCP_A2A_LangGraph_Gradio.ipynb",
             AQUI / "07b_Ejercicio_Tasa_y_Requisitos.ipynb"]   # sesión adicional
REQUIREMENTS = AQUI / "requirements.txt"
ENV_FILE = RAIZ / ".env"
MODELO_POR_DEFECTO = "openai/gpt-oss-120b"
# Los servidores que arrancan los notebooks: MCP (paso 3), A2A (paso 7; el 9998 solo en el 07b) y Gradio (paso 11)
PUERTOS = {8001: "Servidor MCP (paso 3)", 9999: "Agente de Créditos A2A (paso 7)",
           9998: "Agente de Requisitos A2A (07b, paso 7)", 7860: "Gradio (paso 11)"}

PYTHON_MIN = (3, 10)
PYTHON_MAX_PROBADO = (3, 14)
PATRON_CLAVE = re.compile(r"gsk_[A-Za-z0-9]{20,}")

OK, AVISO, ERROR = "✅", "⚠️ ", "❌"
conteo = {OK: 0, AVISO: 0, ERROR: 0}


def informar(nivel: str, mensaje: str, ayuda: str = "") -> None:
    conteo[nivel] += 1
    print(f"  {nivel} {mensaje}")
    if ayuda and nivel != OK:
        print(f"       → {ayuda}")


def seccion(titulo: str) -> None:
    print(f"\n{titulo}")


# ── 1. Intérprete ────────────────────────────────────────────────────────────
def validar_python() -> None:
    seccion("1. Intérprete de Python")
    v = sys.version_info[:3]
    texto = ".".join(map(str, v))
    if v[:2] < PYTHON_MIN:
        informar(ERROR, f"Python {texto} es demasiado antiguo", "usa Python 3.12 o 3.13")
    elif v[:2] > PYTHON_MAX_PROBADO:
        informar(AVISO, f"Python {texto} no está probado",
                 "pandas o pydantic pueden no tener ruedas para esta versión; usa 3.12 o 3.13")
    else:
        informar(OK, f"Python {texto}")

    en_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if en_venv:
        informar(OK, f"entorno virtual activo: {Path(sys.prefix).name}")
    else:
        informar(AVISO, "no estás dentro de un entorno virtual",
                 "Windows: .\\.venv\\Scripts\\Activate.ps1 · macOS: source .venv-mac/bin/activate")


# ── 2. Paquetes ──────────────────────────────────────────────────────────────
def leer_requirements() -> list[tuple[str, str]]:
    requisitos = []
    for linea in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        # Los extras (a2a-sdk[http-server]) no forman parte del nombre del paquete
        m = re.match(r"([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(.*)", linea)
        requisitos.append((m.group(1), m.group(2).strip()))
    return requisitos


def cumple(version: str, especificador: str) -> bool | None:
    # None = no se pudo evaluar (falta `packaging`); se trata como válido.
    if not especificador:
        return True
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
    except ImportError:
        return None
    return Version(version) in SpecifierSet(especificador)


def validar_paquetes() -> None:
    seccion("2. Paquetes (laboratorio-7/requirements.txt)")
    if not REQUIREMENTS.exists():
        informar(ERROR, f"no existe {REQUIREMENTS.name}")
        return
    for nombre, especificador in leer_requirements():
        etiqueta = f"{nombre}{especificador}"
        try:
            version = metadata.version(nombre)
        except metadata.PackageNotFoundError:
            informar(ERROR, f"{etiqueta}: no instalado",
                     "python -m pip install -r laboratorio-7/requirements.txt")
            continue
        resultado = cumple(version, especificador)
        if resultado is False:
            informar(ERROR, f"{etiqueta}: versión instalada {version} fuera de rango",
                     "python -m pip install -r laboratorio-7/requirements.txt")
        else:
            informar(OK, f"{nombre} {version}")

    # Además de estar instalados, comprobamos que se importen (detecta instalaciones rotas).
    for modulo in ("langgraph.graph", "langchain_groq", "mcp", "langchain_mcp_adapters", "a2a",
                   "starlette", "uvicorn", "httpx", "pandas", "dotenv", "gradio", "ipykernel"):
        try:
            __import__(modulo)
        except Exception as exc:  # noqa: BLE001 - queremos reportar cualquier fallo de importación
            informar(ERROR, f"import {modulo} falla: {exc.__class__.__name__}: {exc}")

    # Las piezas que usa el notebook: sus nombres cambiaron entre versiones de los SDK, por eso
    # se comprueban una por una (create_agent es de LangChain 1.x; las rutas A2A, de a2a-sdk 1.x).
    piezas = {
        "LangChain (create_agent, wrap_tool_call)": (
            "from langchain.agents import create_agent\n"
            "from langchain.agents.middleware import wrap_tool_call"),
        "MCP (FastMCP, ClientSession, streamable_http_client)": (
            "from mcp import ClientSession\n"
            "from mcp.server.fastmcp import FastMCP\n"
            "from mcp.client.streamable_http import streamable_http_client"),
        "langchain-mcp-adapters (MultiServerMCPClient)": (
            "from langchain_mcp_adapters.client import MultiServerMCPClient"),
        "a2a-sdk servidor (Agent Card, ejecutor y rutas JSON-RPC)": (
            "from a2a.server.agent_execution import AgentExecutor\n"
            "from a2a.server.request_handlers import DefaultRequestHandler\n"
            "from a2a.server.tasks import InMemoryTaskStore\n"
            "from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes\n"
            "from a2a.types import AgentCard, AgentInterface, AgentSkill, AgentCapabilities\n"
            "from a2a.helpers.proto_helpers import new_text_message"),
        "a2a-sdk cliente (create_client, SendMessageRequest)": (
            "from a2a.client import create_client, ClientConfig\n"
            "from a2a.types import Message, Part, Role, SendMessageRequest"),
    }
    for descripcion, codigo in piezas.items():
        try:
            exec(codigo, {})  # noqa: S102 - código fijo de este script
            informar(OK, descripcion)
        except ImportError as exc:
            informar(ERROR, f"{descripcion}: {exc}",
                     "python -m pip install -U -r laboratorio-7/requirements.txt")


# ── 3. Kernel de Jupyter ─────────────────────────────────────────────────────
def validar_kernel() -> None:
    seccion("3. Kernel de Jupyter")
    try:
        from jupyter_client.kernelspec import KernelSpecManager
    except ImportError:
        informar(AVISO, "jupyter_client no disponible; no se puede listar kernels")
        return
    kernels = KernelSpecManager().find_kernel_specs()
    if "multiagentica" in kernels:
        informar(OK, "kernel 'multiagentica' registrado")
    else:
        informar(AVISO, "kernel 'multiagentica' no registrado (opcional)",
                 'python -m ipykernel install --user --name multiagentica '
                 '--display-name "Python (Multiagentica)"')
    print(f"       Intérprete actual (selecciónalo en VS Code si no ves el kernel): {sys.executable}")


# ── 4. Clave y configuración ─────────────────────────────────────────────────
def leer_env() -> dict[str, str]:
    valores: dict[str, str] = {}
    if not ENV_FILE.exists():
        return valores
    for linea in ENV_FILE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip("'\"")
    return valores


def validar_configuracion() -> dict[str, str]:
    seccion("4. Configuración de Groq (.env en la raíz del repositorio)")
    if not ENV_FILE.exists():
        informar(ERROR, ".env no existe en la raíz", "cp .env.example .env  y completa GROQ_API_KEY")
        return {}
    informar(OK, ".env encontrado")
    valores = leer_env()
    # La variable de entorno del proceso tiene prioridad, igual que en python-dotenv.
    clave = os.getenv("GROQ_API_KEY") or valores.get("GROQ_API_KEY", "")
    if not clave:
        informar(ERROR, "GROQ_API_KEY está vacía o no existe", "agrega GROQ_API_KEY=tu_clave en .env")
    elif clave == "tu_clave_nueva":
        informar(ERROR, "GROQ_API_KEY conserva el valor de la plantilla", "reemplázala por tu clave real")
    elif not clave.startswith("gsk_"):
        informar(AVISO, "GROQ_API_KEY no empieza por 'gsk_' (formato habitual de Groq)",
                 "verifica que copiaste la clave completa")
    else:
        informar(OK, "GROQ_API_KEY configurada (valor no mostrado)")
    # Este notebook fija el modelo (y usa reasoning_effort, que solo aceptan los gpt-oss): GROQ_MODEL no aplica.
    modelo = MODELO_POR_DEFECTO
    informar(OK, f"modelo fijo en el notebook: {modelo}")
    if os.getenv("GROQ_MODEL") or valores.get("GROQ_MODEL"):
        print("       ℹ️  GROQ_MODEL está definido en .env, pero este notebook no lo usa")
    return {"clave": clave if clave and clave != "tu_clave_nueva" else "", "modelo": modelo}


# ── 5. Puertos ───────────────────────────────────────────────────────────────
def validar_puertos() -> None:
    seccion("5. Puertos locales (servidores del notebook)")
    for puerto, servicio in PUERTOS.items():
        with socket.socket() as s:
            ocupado = s.connect_ex(("127.0.0.1", puerto)) == 0
        if not ocupado:
            informar(OK, f"{puerto} libre · {servicio}")
        elif puerto == 7860:
            informar(AVISO, f"{puerto} ocupado · {servicio}",
                     "Gradio usará el siguiente puerto libre; o ejecuta el paso 12 en el kernel que lo abrió")
        else:
            informar(AVISO, f"{puerto} ocupado · {servicio}",
                     "si es un kernel anterior de este notebook, reinícialo: el notebook no arranca "
                     "un servidor nuevo y seguirías usando el código viejo")


# ── 6. Notebooks ─────────────────────────────────────────────────────────────
def validar_notebook(notebook: Path) -> None:
    print(f"  · {notebook.name}")
    if not notebook.exists():
        informar(ERROR, f"no existe {notebook.name}")
        return
    try:
        nb = json.loads(notebook.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        informar(ERROR, f"{notebook.name} no es JSON válido: {exc}")
        return
    celdas = nb.get("cells", [])
    informar(OK, f"JSON válido ({len(celdas)} celdas)")

    fuente = "\n".join("".join(c.get("source", [])) for c in celdas)
    salidas = json.dumps([c.get("outputs", []) for c in celdas if c.get("cell_type") == "code"])
    if PATRON_CLAVE.search(fuente) or PATRON_CLAVE.search(salidas):
        informar(ERROR, "el notebook contiene lo que parece una clave de Groq (gsk_…)",
                 "bórrala del código y de las salidas, y revoca esa clave en la consola de Groq")
    else:
        informar(OK, "no aparece ninguna clave de Groq en el código ni en las salidas")

    if "load_dotenv" in fuente:
        informar(OK, "lee la clave de .env en local y de Secrets en Colab")
    else:
        informar(ERROR, "el notebook no carga .env: solo funcionaría en Colab",
                 "usa load_dotenv() antes de leer GROQ_API_KEY")
    # Ignoramos los comentarios: la guía de la celda menciona «demo.launch(...)» antes de la llamada real.
    sin_comentarios = "\n".join(linea.split("#")[0] for linea in fuente.splitlines())
    lanzamiento = re.search(r"demo\.launch\(([^)]*)\)", sin_comentarios)
    if lanzamiento and re.search(r"share\s*=\s*True", lanzamiento.group(1)):
        informar(AVISO, "demo.launch(share=True): en local crea un enlace público a la interfaz",
                 "cualquiera con el enlace podría gastar tu cuota de Groq; usa share=False fuera de Colab")
    elif lanzamiento:
        informar(OK, f"demo.launch({lanzamiento.group(1)}): sin enlace público fuera de Colab")


# ── 7. Conexión (opcional) ───────────────────────────────────────────────────
def validar_online(config: dict[str, str]) -> None:
    seccion("7. Conexión con Groq (--online; no consume tokens)")
    if not config.get("clave"):
        informar(ERROR, "sin clave válida no se puede probar la conexión")
        return
    try:
        from groq import Groq
        ids = {m.id for m in Groq(api_key=config["clave"]).models.list().data}
    except Exception as exc:  # noqa: BLE001
        informar(ERROR, f"no se pudo consultar Groq: {exc.__class__.__name__}",
                 "revisa tu conexión a internet y que la clave siga activa")
        return
    informar(OK, f"Groq responde ({len(ids)} modelos disponibles)")
    if config["modelo"] in ids:
        informar(OK, f"el modelo '{config['modelo']}' está disponible")
    else:
        informar(ERROR, f"el modelo '{config['modelo']}' no aparece en tu cuenta",
                 "el notebook lo tiene fijo; revisa los modelos de tu cuenta en Groq")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--online", action="store_true", help="comprueba también la conexión con Groq")
    args = parser.parse_args()

    print("Validación del entorno · Laboratorio 7")
    validar_python()
    validar_paquetes()
    validar_kernel()
    config = validar_configuracion()
    validar_puertos()
    seccion("6. Notebooks")
    for notebook in NOTEBOOKS:
        validar_notebook(notebook)
    if args.online:
        validar_online(config)
    else:
        print("\n(Usa --online para probar también la conexión con Groq.)")

    print(f"\nResumen: {conteo[OK]} correctas · {conteo[AVISO]} advertencias · {conteo[ERROR]} errores")
    if conteo[ERROR]:
        print("Corrige los errores ❌ antes de ejecutar el notebook.")
        return 1
    print("Listo para ejecutar el notebook." if not conteo[AVISO] else
          "Puedes ejecutar el notebook; revisa las advertencias ⚠️.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
