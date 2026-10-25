# Laboratorio 0: equipo editorial multiagente

Este laboratorio implementa con **LangGraph** un equipo editorial que redacta,
revisa y evalúa una entrada breve de blog sobre el uso responsable de la IA en
pequeños negocios.

El notebook principal es:

[`00_CASO_RESUELTO_Blog_LangGraph_Groq.ipynb`](./00_CASO_RESUELTO_Blog_LangGraph_Groq.ipynb)

Consulta el [resumen de temas y puntos clave](./resumen.md) antes o después de
ejecutar el notebook.

## Preparar el entorno

Las dependencias están en [`requirements.txt`](./requirements.txt). Un entorno
virtual no es portable entre sistemas operativos: si el repositorio está en una
carpeta sincronizada (por ejemplo OneDrive) y lo usas en Windows y macOS, crea
un entorno distinto en cada sistema.

### Windows (PowerShell, en la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r laboratorio-0/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

### macOS / Linux (terminal, en la raíz del repositorio)

```bash
python3 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install -r laboratorio-0/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

Se recomienda Python 3.13 (probado también con 3.12). Python 3.15 puede
intentar compilar pandas desde código fuente si no existe una rueda compatible.

## Ejecutar en VS Code

1. Abre el notebook desde esta carpeta.
2. Pulsa **Seleccionar kernel** en la esquina superior derecha.
3. Elige **Python (Multiagentica)** o el intérprete del entorno
   (`.venv\Scripts\python.exe` en Windows, `.venv-mac/bin/python` en macOS).
4. Reinicia el kernel.
5. Ejecuta la celda de instalación.
6. Ejecuta las celdas en orden.

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
Después de ejecutar la celda de configuración debe aparecer:

```text
Clave disponible: True
```

Si aparece `False`, verifica que la variable se llame exactamente
`GROQ_API_KEY`, que `.env` exista en la raíz y reinicia el kernel.

Nunca escribas la clave directamente en una celda ni confirmes `.env` en Git.
Si una clave fue compartida públicamente, revócala y crea una nueva.

## Modos de ejecución

- `MODO_SIMULADO = True`: practica el flujo sin llamadas a Groq ni consumo de
  tokens.
- `MODO_SIMULADO = False`: ejecuta llamadas reales al modelo configurado.

El modelo puede cambiarse con la variable opcional `GROQ_MODEL` en `.env`.

El diagrama del grafo (sección 6.1) se genera con un servicio externo y
requiere conexión a internet; si falla, el notebook imprime el código Mermaid.
