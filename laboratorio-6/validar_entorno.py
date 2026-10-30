#!/usr/bin/env python3
"""Valida que el entorno cumpla los requisitos para ejecutar el notebook del laboratorio 6.

Solo usa la biblioteca estándar, así que funciona aunque falten dependencias.
Nunca imprime el valor de la clave de Groq.

Uso (desde la raíz del repositorio, con el entorno virtual activado):

    python laboratorio-6/validar_entorno.py            # comprobaciones locales
    python laboratorio-6/validar_entorno.py --online   # además consulta Groq (sin consumir tokens)

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
NOTEBOOKS = [AQUI / "06a_Multiagente_RAG_Gradio.ipynb"]
REQUIREMENTS = AQUI / "requirements.txt"
ENV_FILE = RAIZ / ".env"
CARPETA_PDF = AQUI / "manual_pdf"          # el manual del reto: 6 PDFs
CARPETA_INDICE = AQUI / "indice_faiss"    # el índice FAISS que crea el paso 5
PDFS_ESPERADOS = 6
MODELO_POR_DEFECTO = "openai/gpt-oss-120b"
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

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
                 "torch o pandas pueden no tener ruedas para esta versión; usa 3.12 o 3.13")
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
    seccion("2. Paquetes (laboratorio-6/requirements.txt)")
    if not REQUIREMENTS.exists():
        informar(ERROR, f"no existe {REQUIREMENTS.name}")
        return
    for nombre, especificador in leer_requirements():
        etiqueta = f"{nombre}{especificador}"
        try:
            version = metadata.version(nombre)
        except metadata.PackageNotFoundError:
            informar(ERROR, f"{etiqueta}: no instalado",
                     "python -m pip install -r laboratorio-6/requirements.txt")
            continue
        resultado = cumple(version, especificador)
        if resultado is False:
            informar(ERROR, f"{etiqueta}: versión instalada {version} fuera de rango",
                     "python -m pip install -r laboratorio-6/requirements.txt")
        else:
            informar(OK, f"{nombre} {version}")

    # Además de estar instalados, comprobamos que se importen (detecta instalaciones rotas).
    for modulo in ("langgraph.graph", "langchain_groq", "langchain_huggingface", "langchain_text_splitters",
                   "sentence_transformers", "faiss", "pypdf", "pydantic", "pandas", "dotenv", "gradio", "ipykernel"):
        try:
            __import__(modulo)
        except Exception as exc:  # noqa: BLE001 - queremos reportar cualquier fallo de importación
            informar(ERROR, f"import {modulo} falla: {exc.__class__.__name__}: {exc}")

    # Los agentes se crean con create_agent (LangChain 1.x); los PDFs se leen con PyPDFLoader y el
    # índice es FAISS (langchain-community).
    try:
        from langchain.agents import create_agent  # noqa: F401
        from langchain_community.document_loaders import PyPDFLoader  # noqa: F401
        from langchain_community.vectorstores import FAISS  # noqa: F401
        informar(OK, "LangChain incluye create_agent, PyPDFLoader y FAISS")
    except ImportError as exc:
        informar(ERROR, f"falta una pieza de LangChain: {exc}",
                 "python -m pip install -U -r laboratorio-6/requirements.txt")


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


# ── 5. Modelo de embeddings ──────────────────────────────────────────────────
def embeddings_en_cache() -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return False
    return isinstance(try_to_load_from_cache(MODELO_EMBEDDINGS, "config.json"), str)


def validar_embeddings() -> None:
    seccion("5. Modelo de embeddings (Hugging Face)")
    if embeddings_en_cache():
        informar(OK, f"{MODELO_EMBEDDINGS} ya está en la caché local")
    else:
        informar(AVISO, f"{MODELO_EMBEDDINGS} aún no está descargado",
                 "el paso 5 del notebook lo descarga (~470 MB, una sola vez); necesitas internet")


# ── 5b. Manual en PDF e índice FAISS ─────────────────────────────────────────
def validar_manual() -> None:
    seccion("5b. Manual en PDF (manual_pdf/) e índice FAISS")
    pdfs = sorted(CARPETA_PDF.glob("*.pdf")) if CARPETA_PDF.exists() else []
    if not pdfs:
        informar(ERROR, f"no hay PDFs en {CARPETA_PDF.name}/", "copia ahí los 6 PDFs del manual")
        return
    nivel = OK if len(pdfs) == PDFS_ESPERADOS else AVISO
    informar(nivel, f"{len(pdfs)} PDFs en {CARPETA_PDF.name}/ (se esperan {PDFS_ESPERADOS})",
             "el notebook indexa todos los PDFs que encuentre en la carpeta")
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    for pdf in pdfs:
        try:
            paginas = PdfReader(pdf).pages
            texto = paginas[0].extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            informar(ERROR, f"{pdf.name}: no se puede leer ({exc.__class__.__name__})")
            continue
        if not texto.strip():
            informar(ERROR, f"{pdf.name}: sin texto extraíble (¿PDF escaneado?)", "el RAG necesita PDFs con texto, no imágenes")
        elif "Vigente desde" not in texto:
            informar(AVISO, f"{pdf.name}: no se encontró 'Vigente desde' en la página 1",
                     "el agente no podrá saber qué norma prevalece en una contradicción")
        else:
            informar(OK, f"{pdf.name}: {len(paginas)} página(s) con texto")
    if (CARPETA_INDICE / "huella.txt").exists():
        print(f"       ℹ️  Hay un índice guardado en {CARPETA_INDICE.name}/; el paso 5 lo reutiliza si los PDFs no cambiaron")
    else:
        print(f"       ℹ️  Aún no hay índice en {CARPETA_INDICE.name}/; el paso 5 lo creará")


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
    lanzamiento = re.search(r"demo\.launch\(([^)]*)\)", fuente)
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

    from urllib.request import urlopen
    if not embeddings_en_cache():
        try:
            urlopen(f"https://huggingface.co/{MODELO_EMBEDDINGS}", timeout=8)
            informar(OK, "huggingface.co accesible (descarga del modelo de embeddings)")
        except Exception:  # noqa: BLE001
            informar(ERROR, "huggingface.co no accesible y el modelo de embeddings no está en caché",
                     "el paso 5 no podrá crear el índice; revisa tu conexión o el proxy")
    try:
        urlopen("https://mermaid.ink", timeout=8)
        informar(OK, "mermaid.ink accesible (diagrama del grafo, paso 11)")
    except Exception:  # noqa: BLE001
        informar(AVISO, "mermaid.ink no accesible",
                 "el notebook imprimirá el código Mermaid en lugar del PNG; es opcional")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--online", action="store_true", help="comprueba también la conexión con Groq")
    args = parser.parse_args()

    print("Validación del entorno · Laboratorio 6")
    validar_python()
    validar_paquetes()
    validar_kernel()
    config = validar_configuracion()
    validar_embeddings()
    validar_manual()
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
