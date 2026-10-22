# Arquitecturas en Inteligencia Artificial Multiagéntica

Colección de proyectos y casos prácticos para estudiar arquitecturas
multiagente con Python, LangGraph y modelos de lenguaje.

## Proyecto actual

**`00_CASO_RESUELTO_Blog_LangGraph_Groq.ipynb`**

Implementa un equipo editorial multiagente con LangGraph y Groq. El flujo
incluye escritor, revisores especializados, metarrevisor y evaluador.
También permite ejecutar el caso en modo simulado, sin llamadas al modelo.

## Preparar el entorno en VS Code

Desde una terminal PowerShell abierta en la raíz del repositorio:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "langgraph>=1,<2" "groq>=0.30" "pydantic>=2,<3" "pandas==2.2.3" "python-dotenv>=1,<2" ipykernel
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

En VS Code, abre el notebook y selecciona el kernel **Python (Multiagentica)**.

## Configurar Groq

1. Revoca cualquier clave que se haya compartido públicamente y crea una nueva
   en la consola de Groq.
2. Crea un archivo `.env` en esta carpeta con esta estructura:

   ```text
   GROQ_API_KEY=tu_clave_nueva
   ```

3. No publiques `.env`: está protegido por `.gitignore`.
4. Ejecuta primero la celda de instalación y después la celda de configuración.
   El notebook carga `.env` con `python-dotenv` y comprueba la presencia de la
   variable sin imprimir su valor:

   ```python
   import os
   print("Clave disponible:", bool(os.getenv("GROQ_API_KEY")))
   ```

   El resultado esperado es `Clave disponible: True`.

## Modos de ejecución

- `MODO_SIMULADO = True`: no llama a Groq y no consume tokens.
- `MODO_SIMULADO = False`: ejecuta los agentes con el modelo configurado.

El modelo se puede cambiar mediante la variable opcional `GROQ_MODEL` en `.env`.

## Seguridad y colaboración

- Nunca escribas claves directamente en el notebook.
- Nunca confirmes `.env`, salidas con secretos ni credenciales en Git.
- Usa `.env.example` únicamente para documentar nombres de variables, sin valores
  reales.
- Cada nuevo proyecto puede añadirse como un notebook o carpeta independiente,
  manteniendo sus dependencias y documentación claras.
