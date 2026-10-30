# Laboratorio 6: la sucursal multiagente con RAG

Este laboratorio es un **caso resuelto** que continúa la sucursal bancaria
ficticia del laboratorio 5. Un **Supervisor** coordina tres agentes y uno de
ellos, el **Agente de Políticas**, busca en el manual de la sucursal antes de
responder: eso es **RAG** (*Retrieval-Augmented Generation*). Los otros dos
agentes consultan la cuenta ficticia y simulan la cuota con Python. Incluye una
interfaz en **Gradio** con un diagrama de secuencia de la colaboración y la
tabla de fragmentos que recuperó el RAG.

El notebook incluye resuelto el **reto de la Parte A**: el manual ya no son 4
archivos `.md` cortos en memoria, sino **6 PDFs** (carpeta
[`manual_pdf/`](./manual_pdf/)) indexados en **FAISS**, un índice que se guarda
en disco para no recalcular los embeddings en cada ejecución. El agente cita
**archivo y página**. El código original sigue en las celdas, comentado, junto
al nuevo, que explica qué hace cada cambio y por qué.

El notebook principal es:

[`06a_Multiagente_RAG_Gradio.ipynb`](./06a_Multiagente_RAG_Gradio.ipynb)

Consulta el [resumen de temas y puntos clave](./resumen.md) antes o después de
ejecutarlo. Todo es ficticio: políticas, tasas y clientes son inventados para
la clase, y el ejemplo no aprueba créditos.

> 📄 El notebook de la siguiente sesión, `06_MCP_A2A_LangGraph_Gradio.ipynb`, no
> está incluido en esta carpeta.

## Preparar el entorno

Las dependencias están en [`requirements.txt`](./requirements.txt). Son las del
laboratorio 5 **más LangChain y el modelo de embeddings**
(`langchain`, `langchain-groq`, `langchain-huggingface`,
`langchain-text-splitters` y `sentence-transformers`, que instala PyTorch) **y,
para el reto, `pypdf`, `langchain-community` y `faiss-cpu`**, así
que si reutilizas el entorno virtual debes volver a instalar los requisitos de
esta carpeta. La instalación descarga alrededor de 1 GB. Un entorno virtual no
es portable entre sistemas operativos: si usas el repositorio en Windows y
macOS, crea un entorno distinto en cada sistema.

### Windows (PowerShell, en la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r laboratorio-6/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

### macOS / Linux (terminal, en la raíz del repositorio)

```bash
python3 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install -r laboratorio-6/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

Se recomienda Python 3.13 (probado en Windows con Python 3.13.2, LangChain 1.4,
LangGraph 1.2, langchain-community 0.4, faiss-cpu 1.15, sentence-transformers
5.7 y Gradio 6.31).

## Configurar Groq

Este notebook **no tiene modo simulado**: el Supervisor y los agentes usan
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

Los **embeddings no usan Groq**: el modelo
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` corre en tu
equipo, sin clave. La primera ejecución del paso 5 lo descarga (~470 MB) a la
caché de Hugging Face; las siguientes lo leen de allí.

## Validar los requisitos antes de ejecutar

Con el entorno activo, desde la raíz del repositorio:

```bash
python laboratorio-6/validar_entorno.py            # comprobaciones locales
python laboratorio-6/validar_entorno.py --online   # además consulta Groq
```

El script no consume tokens y nunca imprime la clave. Comprueba la versión de
Python y el entorno virtual, los paquetes de `requirements.txt`, que LangChain
incluya `create_agent`, `PyPDFLoader` y `FAISS`, el kernel, el `.env`, si el
modelo de embeddings ya está descargado, que `manual_pdf/` tenga los 6 PDFs con
texto extraíble y su fecha de vigencia, y que el notebook sea válido, lea la
clave de `.env`, no contenga ninguna clave `gsk_…` y no cree un enlace público
con `demo.launch()` fuera de Colab. Con `--online` comprueba además Groq,
Hugging Face (si falta el modelo) y el servicio de diagramas. Termina con
código 0 si no hay errores y con 1 si hay alguno.

## Ejecutar en VS Code

1. Abre el notebook desde esta carpeta.
2. Pulsa **Seleccionar kernel** en la esquina superior derecha.
3. Elige **Python (Multiagentica)** o el intérprete del entorno
   (`.venv\Scripts\python.exe` en Windows, `.venv-mac/bin/python` en macOS).
4. Reinicia el kernel.
5. Ejecuta las celdas en orden, de los pasos 0 al 13.

| Paso | Qué ocurre |
|---|---|
| 0 | Instala solo lo que falte (en local, si ya instalaste `requirements.txt`, no descarga nada) |
| 1 | Conecta con Groq usando la clave de `.env`: debe imprimir `conectado` |
| 3 | Lista los 6 PDFs de `manual_pdf/` |
| 4 | Carga cada PDF página por página, quita el encabezado repetido y lo divide en 24 fragmentos con archivo, página, código y vigencia |
| 5 | Descarga el modelo de embeddings (solo la primera vez) y **crea** el índice FAISS en `indice_faiss/`, o lo **carga** si los PDFs no cambiaron |
| 6 | Prueba la búsqueda sola, sin LLM: muestra archivo, página y vigencia |
| 8 | Prueba el Agente de Políticas por sí solo |
| 10 | Ejecuta la pregunta mixta sin interfaz y muestra la bitácora |
| 11 | Dibuja el grafo |
| 12 | Abre la interfaz en `http://127.0.0.1:7860` (o el siguiente puerto libre) |
| 13 | Cierra el servidor de Gradio |

### El índice FAISS en disco

| Archivo en `indice_faiss/` | Qué guarda |
|---|---|
| `index.faiss` | Los vectores (uno por fragmento) |
| `index.pkl` | Los textos y metadatos de cada fragmento |
| `huella.txt` | Un *hash* de los PDFs, de los parámetros de división y del modelo |

En cada ejecución el paso 5 recalcula la huella: si coincide, **carga** el
índice (≈ 0,05 s) sin recalcular embeddings; si cambiaste un PDF, agregaste uno
o modificaste `TAMANO_FRAGMENTO`, la huella cambia y el índice se reconstruye
solo. Para forzarlo, borra la carpeta. `indice_faiss/` es generada y está
excluida de Git; los PDFs de `manual_pdf/` sí se versionan.

`index.pkl` se lee con `pickle`, que puede ejecutar código al cargarse; por eso
`FAISS.load_local` exige `allow_dangerous_deserialization=True`. Es seguro solo
porque el índice lo crea el propio notebook: nunca cargues un índice descargado.

La versión original (comentada) creaba la carpeta `manual/`; quedó excluida de
Git por si la vuelves a activar.

### La interfaz de Gradio en local

- En local la interfaz **no** crea un enlace público: solo es accesible desde tu
  equipo. En Colab sí se crea (`share=True`), porque es la única forma de
  abrirla desde allí.
- VS Code puede mostrarla dentro del notebook. Si no se ve, abre en el navegador
  la URL local que imprime el paso 12.
- La celda del paso 12 termina enseguida, pero el servidor sigue activo hasta
  que ejecutes el paso 13 o reinicies el kernel. Si cambias código, ejecuta el
  paso 13, vuelve a ejecutar lo que cambiaste y después el paso 12.
- Al importar Gradio o sentence-transformers pueden aparecer avisos como
  `TqdmWarning: IProgress not found` o, en Windows, uno de Hugging Face sobre
  enlaces simbólicos en la caché. Son inofensivos. Lo mismo vale para el
  `DeprecationWarning` de `langchain-community`, que anuncia su retiro futuro:
  en las versiones fijadas en `requirements.txt` `PyPDFLoader` y `FAISS`
  funcionan.

## Costo en llamadas a Groq

Cada agente es un `create_agent` que llama al LLM al menos dos veces (decidir
la herramienta y redactar), y el Supervisor decide una vez por agente más la
decisión de finalizar.

| Parte | Llamadas aproximadas |
|---|---|
| Ejecución completa del notebook (pasos 1 a 10) | ~14 |
| Interfaz: «¿Cuánto saldo tengo?» (un agente) | ~5 |
| Interfaz: pregunta mixta de la moto (tres agentes) | ~11 |

Si recibes un error 429 (límite de peticiones), espera unos segundos y repite.
Como decide un LLM, **el orden** de los agentes y las consultas al manual
pueden variar entre ejecuciones; la cuota la calcula Python
(≈ **$498.215** para $15.000.000 a 36 meses al 1 %). Con el manual en PDF el
aporte mínimo para motos nuevas es **15 %** ($3.000.000), según la circular
vigente desde el 1-09-2026, y no el 10 % del manual MCV-003. Los embeddings no
consumen llamadas a Groq.

## Ejecutar en Google Colab

El notebook funciona en Colab sin cambios: si no encuentra `.env`, lee la clave
de los Secrets, no reinstala `sentence-transformers`, `gradio` ni `pandas`, y
crea el enlace público de la interfaz.

1. Sube el `.ipynb` a Colab (**Archivo → Subir notebook**) y, en el panel 📁
   **Archivos**, crea la carpeta `manual_pdf` y sube allí los 6 PDFs.
2. Abre el panel 🔑 **Secrets**, crea `GROQ_API_KEY` con tu clave y activa
   **Acceso del notebook**.
3. Ejecuta las celdas en orden.

En Colab el modelo de embeddings se descarga en cada sesión nueva, y
`indice_faiss/` se pierde al cerrar la sesión (el paso 5 lo vuelve a crear). El diagrama
del paso 11 se genera con un servicio externo y requiere conexión a internet;
si falla, el notebook imprime el código Mermaid.
