#!/usr/bin/env python3
"""Valida que el entorno cumpla los requisitos para ejecutar el notebook del laboratorio 5.

Solo usa la biblioteca estándar, así que funciona aunque falten dependencias.
Nunca imprime el valor de la clave de Groq.

Uso (desde la raíz del repositorio, con el entorno virtual activado):

    python laboratorio-5/validar_entorno.py            # comprobaciones locales
    python laboratorio-5/validar_entorno.py --online   # además consulta Groq (sin consumir tokens)

Código de salida: 0 si no hay errores (las advertencias no cuentan), 1 si hay errores.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from importlib import metadata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
NOTEBOOKS = [AQUI / "05_Sucursal_Bancaria_Gradio_Resuelto.ipynb",   # caso resuelto de la clase
             AQUI / "05b_Oficina_Anteproyecto_CacaoIA.ipynb"]       # versión alterna
REQUIREMENTS = AQUI / "requirements.txt"
ENV_FILE = RAIZ / ".env"
MODELO_POR_DEFECTO = "openai/gpt-oss-120b"

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
                 "pandas puede intentar compilarse desde código fuente; usa 3.12 o 3.13")
    else:
        informar(OK, f"Python {texto}")

    en_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if en_venv:
        informar(OK, f"entorno virtual activo: {Path(sys.prefix).name}")
    else:
        informar(AVISO, "no estás dentro de un entorno virtual",
                 "crea uno: python3 -m venv .venv-mac && source .venv-mac/bin/activate")


# ── 2. Paquetes ──────────────────────────────────────────────────────────────
def leer_requirements() -> list[tuple[str, str]]:
    requisitos = []
    for linea in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        m = re.match(r"([A-Za-z0-9_.\-]+)\s*(.*)", linea)
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
    seccion("2. Paquetes (laboratorio-5/requirements.txt)")
    if not REQUIREMENTS.exists():
        informar(ERROR, f"no existe {REQUIREMENTS.name}")
        return
    for nombre, especificador in leer_requirements():
        etiqueta = f"{nombre}{especificador}"
        try:
            version = metadata.version(nombre)
        except metadata.PackageNotFoundError:
            informar(ERROR, f"{etiqueta}: no instalado",
                     "python -m pip install -r laboratorio-5/requirements.txt")
            continue
        resultado = cumple(version, especificador)
        if resultado is False:
            informar(ERROR, f"{etiqueta}: versión instalada {version} fuera de rango",
                     "python -m pip install -r laboratorio-5/requirements.txt")
        else:
            informar(OK, f"{nombre} {version}")

    # Además de estar instalados, comprobamos que se importen (detecta instalaciones rotas).
    for modulo in ("langgraph.graph", "groq", "pydantic", "pandas", "dotenv", "gradio", "ipykernel"):
        try:
            __import__(modulo)
        except Exception as exc:  # noqa: BLE001 - queremos reportar cualquier fallo de importación
            informar(ERROR, f"import {modulo} falla: {exc.__class__.__name__}: {exc}")

    # La interfaz se redibuja con los avisos que los nodos envían por get_stream_writer().
    try:
        from langgraph.config import get_stream_writer  # noqa: F401
        informar(OK, "LangGraph incluye get_stream_writer (avisos para la interfaz)")
    except ImportError as exc:
        informar(ERROR, f"falta get_stream_writer en LangGraph: {exc}",
                 "python -m pip install -U -r laboratorio-5/requirements.txt")


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


# ── 5. Notebooks ─────────────────────────────────────────────────────────────
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

    # Este notebook no tiene modo simulado: todas las decisiones las toma Groq.
    if "MODO_SIMULADO" not in fuente:
        print("       ℹ️  Sin modo simulado: el notebook necesita GROQ_API_KEY para ejecutarse")
    lanzamiento = re.search(r"demo\.launch\(([^)]*)\)", fuente)
    if lanzamiento and re.search(r"share\s*=\s*True", lanzamiento.group(1)):
        informar(AVISO, "demo.launch(share=True): en local crea un enlace público a la interfaz",
                 "cualquiera con el enlace podría gastar tu cuota de Groq; usa share=False fuera de Colab")
    elif lanzamiento:
        informar(OK, f"demo.launch({lanzamiento.group(1)}): sin enlace público fuera de Colab")


# ── 6. Conexión (opcional) ───────────────────────────────────────────────────
def validar_online(config: dict[str, str]) -> None:
    seccion("6. Conexión con Groq (--online; no consume tokens)")
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
                 "los notebooks de este laboratorio lo tienen fijo; revisa los modelos de tu cuenta en Groq")

    try:
        from urllib.request import urlopen
        urlopen("https://mermaid.ink", timeout=8)
        informar(OK, "mermaid.ink accesible (diagramas de los grafos, paso 11)")
    except Exception:  # noqa: BLE001
        informar(AVISO, "mermaid.ink no accesible",
                 "el notebook imprimirá el código Mermaid en lugar del PNG; es opcional")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--online", action="store_true", help="comprueba también la conexión con Groq")
    args = parser.parse_args()

    print("Validación del entorno · Laboratorio 5")
    validar_python()
    validar_paquetes()
    validar_kernel()
    config = validar_configuracion()
    seccion("5. Notebooks")
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
