# Laboratorio 5: la sucursal bancaria multiagente (router, supervisor y jerarquía)

Este laboratorio es un **caso resuelto** de la sesión 3. Usa **el mismo cliente
ficticio y las mismas herramientas** en tres arquitecturas (Router, Supervisor y
Jerárquica) para observar **quién decide a quién llamar** y **quién recibe los
resultados**. Las decisiones las toma un LLM de Groq; los números (saldo, cuota,
límite) los calcula Python. Incluye una interfaz en **Gradio** que muestra en
vivo qué participante está trabajando.

El notebook principal es:

[`05_Sucursal_Bancaria_Gradio_Resuelto.ipynb`](./05_Sucursal_Bancaria_Gradio_Resuelto.ipynb)

Consulta el [resumen de temas y puntos clave](./resumen.md) antes o después de
ejecutarlo. Todo es ficticio: el ejemplo informa y calcula, pero no aprueba
créditos ni mueve dinero.

> 📄 El ejercicio de clase está en `05_Ejercicio_Sucursal_Bancaria.docx`, que
> no está incluido en esta carpeta.

La carpeta incluye además una **versión alterna** con un problema propio, la
oficina del anteproyecto basada en cacaoia-utp. Se describe al final de este
documento.

## Preparar el entorno

Las dependencias están en [`requirements.txt`](./requirements.txt). Son las de
los laboratorios anteriores **más Gradio**, así que si reutilizas el entorno
virtual debes volver a instalar los requisitos de esta carpeta. Un entorno
virtual no es portable entre sistemas operativos: si usas el repositorio en
Windows y macOS, crea un entorno distinto en cada sistema.

### Windows (PowerShell, en la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r laboratorio-5/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

### macOS / Linux (terminal, en la raíz del repositorio)

```bash
python3 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install -r laboratorio-5/requirements.txt
python -m ipykernel install --user --name multiagentica --display-name "Python (Multiagentica)"
```

Se recomienda Python 3.13 (probado también con 3.12, con Gradio 6.30).

## Configurar Groq

Este notebook **no tiene modo simulado**: todas las decisiones las toma Groq,
así que la clave es obligatoria. El archivo `.env` debe estar en la raíz del
repositorio; puedes crearlo a partir de la plantilla
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
python laboratorio-5/validar_entorno.py            # comprobaciones locales
python laboratorio-5/validar_entorno.py --online   # además consulta Groq
```

El script no consume tokens y nunca imprime la clave. Comprueba la versión de
Python y el entorno virtual, los paquetes de `requirements.txt` (incluido
Gradio), que LangGraph incluya `get_stream_writer`, el kernel, el `.env`, y que
los dos notebooks (el resuelto y la versión alterna) sean válidos, no contengan
ninguna clave `gsk_…` y no creen un enlace público con `demo.launch()` fuera de
Colab. Termina con código 0 si no hay errores
y con 1 si hay alguno.

## Ejecutar en VS Code

1. Abre el notebook desde esta carpeta.
2. Pulsa **Seleccionar kernel** en la esquina superior derecha.
3. Elige **Python (Multiagentica)** o el intérprete del entorno
   (`.venv\Scripts\python.exe` en Windows, `.venv-mac/bin/python` en macOS).
4. Reinicia el kernel.
5. Ejecuta las celdas en orden, de los pasos 0 al 14.

| Paso | Qué ocurre |
|---|---|
| 1 | Conecta con Groq usando la clave de `.env` |
| 4 | Prueba de conexión: debe imprimir `texto='hola'` |
| 12 | Ejecuta una solicitud sin interfaz y muestra la bitácora (quién le habló a quién) |
| 13 | Construye la interfaz de Gradio |
| 14 | Abre la interfaz en `http://127.0.0.1:7860` (o el siguiente puerto libre) |
| 15 | Cierra el servidor de Gradio |
| Anexo | Las tres arquitecturas escritas "a mano", sin fábricas ni Gradio |

### La interfaz de Gradio en local

- En local la interfaz **no** crea un enlace público: solo es accesible desde tu
  equipo. En Colab sí se crea (`share=True`), porque es la única forma de
  abrirla desde allí.
- VS Code puede mostrarla dentro del notebook. Si no se ve, abre en el navegador
  la URL local que imprime el paso 14.
- La celda del paso 14 termina enseguida, pero el servidor sigue activo hasta
  que ejecutes el paso 15 o reinicies el kernel. Si cambias código, ejecuta el
  paso 15, vuelve a ejecutar lo que cambiaste, después el paso 13 y el 14.
- Al importar Gradio puede aparecer `TqdmWarning: IProgress not found`. Es un
  aviso inofensivo de una dependencia y no afecta a la interfaz.

## Costo en llamadas a Groq

| Parte | Llamadas aproximadas |
|---|---|
| Ejecución completa del notebook (pasos 0 a 12 y anexo) | ~24 |
| Interfaz: «¿Cuánto saldo tengo disponible?» | 2 (Router) · 4 (Supervisor) · 6 (Jerárquica) |
| Interfaz: consulta mixta (ahorros + moto + requisitos) | ~4 (Router) · ~8 (Supervisor) · ~12 (Jerárquica) |

Si recibes un error 429 (límite de peticiones), espera unos segundos y repite.
Como decide un LLM, **el orden** de los especialistas puede variar entre
ejecuciones; **los números no cambian**, porque los calcula Python.

## Ejecutar en Google Colab

El notebook funciona en Colab sin cambios: si no encuentra `.env`, lee la clave
de los Secrets, no reinstala `gradio`, `pydantic` ni `pandas`, y crea el enlace
público de la interfaz.

1. Sube el `.ipynb` a Colab (**Archivo → Subir notebook**).
2. Abre el panel 🔑 **Secrets**, crea `GROQ_API_KEY` con tu clave y activa
   **Acceso del notebook**.
3. Ejecuta las celdas en orden.

Los diagramas del paso 11 se generan con un servicio externo y requieren
conexión a internet; si falla, el notebook imprime el código Mermaid.

## Versión alterna: la oficina del anteproyecto

Siguiendo la recomendación de la profesora de plantear una versión con un
problema propio, la carpeta incluye:

| Archivo | Qué es |
|---|---|
| [`05b_Oficina_Anteproyecto_CacaoIA.ipynb`](./05b_Oficina_Anteproyecto_CacaoIA.ipynb) | Notebook resuelto: las mismas tres arquitecturas aplicadas a un equipo que revisa un anteproyecto de maestría antes de enviarlo al director |
| [`05b_Ejercicio_Oficina_Anteproyecto.md`](./05b_Ejercicio_Oficina_Anteproyecto.md) | Enunciado: predecir, ejecutar y registrar la traza, cambiar un parámetro, agregar un quinto especialista, ADR breve y un reto opcional |

La organización se basa en **cacaoia-utp**, el entorno multiagente con el que
se redacta un anteproyecto de maestría: un orquestador que decide qué
especialista invocar, auditores que solo emiten informes y chequeos
deterministas. **Los datos son ficticios** (anteproyecto `AP-DEMO`).

| Lab 5 (banco) | Versión alterna |
|---|---|
| Área de Cuentas: Saldos, Movimientos | Área de Documento: Verificador de citas, Auditor de coherencia |
| Área de Créditos: Simulación, Requisitos | Área de Diseño: Auditor metodológico, Crítico de viabilidad |
| Supervisor / Director | Orquestador del anteproyecto |
| Python calcula saldo, cuota y límite | Python calcula los hallazgos (BLOQUEANTE, GRAVE, AVISO) |
| No aprueba créditos | No aprueba el anteproyecto: decide el director de tesis |
| Controles: precio, aporte, meses, ingreso, obligaciones | Controles: muestras, pliegues, páginas, horas de cómputo y disponibles |

Se prepara y ejecuta igual que el notebook resuelto: mismo entorno, mismo
`.env` y los mismos pasos 0 a 15. Con los controles por defecto, la revisión
completa da 2 bloqueantes, 4 graves y 2 avisos. Una ejecución completa del
notebook hace unas 11 llamadas a Groq; en la interfaz, la revisión completa
cuesta alrededor de 5 llamadas con Router, 10 con Supervisor y 14 con
Jerárquica.
