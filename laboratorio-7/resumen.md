# Resumen del Laboratorio 7

## Propósito

El notebook es un **caso resuelto** que continúa la sucursal bancaria ficticia
de los laboratorios 5 y 6. Hasta ahora todos los agentes y sus herramientas
vivían en el mismo programa. Aquí el sistema se separa en piezas que se
comunican con **protocolos estándar**, como lo harían si las construyeran
equipos distintos:

- **MCP** (*Model Context Protocol*): un agente usa **herramientas y datos**
  que expone un servidor.
- **A2A** (*Agent2Agent Protocol*): un agente le **delega una tarea a otro
  agente**, que razona con su propio LLM.

La pregunta de referencia es mixta: «¿Cuánto saldo tengo? Y simula una moto de
20.000.000 con aporte de 5.000.000 a 36 meses». El saldo llega por MCP y la
simulación por A2A.

## Temas principales

### 1. La arquitectura: tres piezas y dos protocolos

| Pieza | Herramientas | Protocolo | Dónde escucha |
|---|---|---|---|
| 🧑‍💼 Asesor | Las 2 del servidor MCP + `consultar_agente_creditos` | — | (dentro del notebook) |
| 🗄️ Servidor MCP "Core bancario" | `consultar_saldo`, `listar_movimientos` | MCP (*streamable HTTP*) | `http://127.0.0.1:8001/mcp` |
| 🤖 Agente de Créditos | `simular_cuota` (local, Python) | A2A (JSON-RPC) | `http://127.0.0.1:9999/` |

**Regla corta:** MCP para **hacer cosas**; A2A para **pedirle a alguien que
haga cosas**. Se complementan: un agente A2A podría usar MCP por dentro.

### 2. MCP: herramientas para cualquier agente (Parte A)

| | MCP |
|---|---|
| Servidor | `FastMCP` convierte funciones en herramientas con `@servidor_mcp.tool()` |
| Qué publica | Nombre (de la función), descripción (el *docstring*) y esquema JSON de entrada (los tipos) |
| Protocolo | `initialize` → `tools/list` → `tools/call` |
| Cliente «a mano» | `ClientSession` + `streamable_http_client` del SDK `mcp` |
| Cliente para agentes | `MultiServerMCPClient` (`langchain-mcp-adapters`) convierte cada herramienta MCP en una herramienta de LangChain |

El servidor **no sabe nada de LangChain ni de Groq**: cualquier cliente MCP
(Claude Desktop, VS Code, otro framework) podría usarlo. El cliente
**descubre** las herramientas con `tools/list`; nadie se las declara de
antemano.

Un detalle técnico: MCP devuelve el resultado en **bloques de contenido** y
Groq espera texto. El *middleware* `resultado_como_texto` (`@wrap_tool_call`)
se pone entre la herramienta y el LLM y convierte los bloques a texto.

### 3. A2A: un agente le pide trabajo a otro (Parte B)

Para que otros lo encuentren y le hablen, el Agente de Créditos publica tres
piezas:

| Pieza | Para qué | En el código |
|---|---|---|
| **Agent Card** | Tarjeta de presentación: nombre, *skills*, dirección y versión del protocolo | `AgentCard(...)` en `/.well-known/agent-card.json` |
| **Ejecutor** | Qué hacer al recibir un mensaje: invocar al agente de LangGraph y devolver su respuesta | `EjecutorCreditos(AgentExecutor)` |
| **Rutas HTTP** | `GET` de la tarjeta y `POST /` para los mensajes JSON-RPC | `create_agent_card_routes` + `create_jsonrpc_routes` |

Un mensaje A2A tiene `role` (`ROLE_USER` o `ROLE_AGENT`) y una lista de
`parts` (texto, datos, archivos). El paso 8 lo arma a mano con el método
`SendMessage`; el paso 9 usa el cliente del SDK (`create_client`), que lee la
Agent Card y elige cómo hablar.

La herramienta `simular_cuota` es **local** del Agente de Créditos: el Asesor
no la ve ni sabe que existe. Solo recibe la respuesta en texto.

### 4. MCP frente a A2A

| | MCP | A2A |
|---|---|---|
| Conecta | Agente ↔ herramientas y datos | Agente ↔ otro agente |
| El otro lado… | **No piensa**: ejecuta una función | **Piensa**: tiene su propio LLM y decide cómo resolver |
| Descubrimiento | `tools/list` | Agent Card |
| Llamada | `tools/call` | `SendMessage` → `Message` o `Task` |
| Respuesta | Datos estructurados (`{"saldo_cop": 5000000}`) | Texto redactado por otro LLM |
| Analogía | Un enchufe universal | Un teléfono entre colegas |

### 5. Todo junto: el Asesor (Parte C)

El Asesor es un `create_agent` con **tres herramientas**. Para su LLM las tres
se ven igual; por debajo viajan por protocolos distintos. Delegar en otro
agente es, para el LLM, **una herramienta más** (`@tool` que envuelve la
llamada A2A). Con la pregunta mixta, el LLM puede pedir ambas herramientas a la
vez y se ejecutan en paralelo, por eso las flechas de la interfaz pueden
intercalarse.

### 6. Observar la colaboración

Cada participante deja un registro en la **bitácora** (`registrar(de, para,
protocolo, accion, detalle)`). La interfaz de Gradio dibuja un diagrama de
secuencia con un carril por participante y un color por protocolo (🟦 usuario,
🟩 MCP, 🟪 A2A, 🟧 herramienta local) y lo redibuja cada 0,4 s mientras el
Asesor trabaja.

### 7. Servidores en el mismo kernel

| Detalle | Por qué importa |
|---|---|
| `uvicorn` en un hilo (`daemon=True`) | El notebook sigue libre mientras los servidores escuchan |
| *Streamable HTTP* en lugar de *stdio* | Con *stdio* el cliente lanzaría el servidor como otro proceso y no compartiría la bitácora |
| Si el puerto está ocupado no arranca otro | Re-ejecutar no duplica servidores, pero tampoco aplica cambios: hay que reiniciar el kernel |
| Solo `127.0.0.1` | Los servidores no son accesibles desde otros equipos |

## Puntos clave a considerar

1. **El protocolo desacopla.** Si mañana el Agente de Créditos se reescribe en
   otro framework, el Asesor no cambia mientras respete A2A. Lo mismo vale para
   el servidor MCP.
2. **Descubrir en vez de declarar.** Una herramienta nueva en el servidor MCP
   (`consultar_tasa`) aparece sola en el Asesor tras reiniciar: la descubre con
   `tools/list`.
3. **Herramienta o agente.** Una herramienta conviene cuando basta una función;
   un agente, cuando la tarea necesita razonar, varios pasos o su propio equipo
   de herramientas.
4. **La descripción es la interfaz para el LLM.** El *docstring* de la
   herramienta MCP y la descripción de la Agent Card son lo que el LLM lee para
   decidir qué usar.
5. **Cada agente piensa con su propio LLM.** Una delegación A2A cuesta llamadas
   adicionales a Groq; una llamada MCP no.
6. **Servidores de terceros son una frontera de confianza.** Un servidor MCP o
   un agente A2A externo exige autenticación, permisos y cuidado con los datos
   sensibles; este ejemplo no tiene ninguno porque todo es local y ficticio.

## Límites del ejemplo

Clientes, saldos y tasas son ficticios; el ejemplo no aprueba créditos. Los
servidores no tienen autenticación y corren en hilos del mismo kernel, algo
útil para la clase pero no para producción. El Agente de Créditos responde con
un `Message` de una sola vez (sin *streaming* ni `Task` de larga duración). La
**respuesta final pasa por el LLM** del Asesor, que puede reformular las cifras
que le devolvieron MCP y A2A: conviene contrastarla con la bitácora.

## Sesión adicional: el ejercicio resuelto

El notebook [`07b_Ejercicio_Tasa_y_Requisitos.ipynb`](./07b_Ejercicio_Tasa_y_Requisitos.ipynb)
resuelve las dos partes del ejercicio y vuelve a levantar todas las piezas, así
que no depende del notebook 07.

| Pieza | Herramientas | Protocolo | Dónde escucha |
|---|---|---|---|
| 🧑‍💼 Asesor | Las 3 del servidor MCP + `consultar_agente_creditos` + `consultar_agente_requisitos` | — | (dentro del notebook) |
| 🗄️ Servidor MCP "Core bancario" | `consultar_saldo`, `listar_movimientos`, 🆕 `consultar_tasa` | MCP | `http://127.0.0.1:8001/mcp` |
| 🤖 Agente de Créditos | `simular_cuota` (local) | A2A | `http://127.0.0.1:9999/` |
| 📋 🆕 Agente de Requisitos | `verificar_requisitos` (local) | A2A | `http://127.0.0.1:9998/` |

### Lo que demuestra cada parte

| | Parte 1 · `consultar_tasa` (MCP) | Parte 2 · Agente de Requisitos (A2A) |
|---|---|---|
| Qué se escribe | Una función con `@servidor_mcp.tool()` | Una Agent Card, un agente y una herramienta `@tool` en el Asesor |
| Cambios en el Asesor | **Ninguno**: llega con `get_tools()` | La herramienta nueva y una frase en sus instrucciones |
| Idea | Descubrir en vez de declarar | Delegar en otro agente es una herramienta más |

- **El paso 7 como receta.** `publicar_a2a(nombre, descripcion, skill,
  crear_agente, puerto)` arma la Agent Card, el ejecutor y las rutas. Lo único
  que cambia de un agente a otro son los datos de la tarjeta y el agente que
  trabaja; el protocolo es el mismo.
- **Una sola fuente para las reglas.** `POLITICA_FICTICIA` (tasa del 1 %,
  35 % del ingreso, documentos) es la del laboratorio 5 y la comparten
  `consultar_tasa`, `simular_cuota` y `verificar_requisitos`. Funciona porque
  todo corre en el mismo kernel; el reto opcional 1 propone que el Agente de
  Créditos lea la tasa por MCP, como haría en producción.
- **El orden importa.** Para saber si la cuota ($498.215) cabe en el límite
  ($525.000), el Asesor debe pedir primero la cuota y enviarla después a
  Requisitos. Sus instrucciones lo indican, pero lo decide el LLM: si pide ambas
  a la vez, Requisitos solo da el límite y la comparación la hace el Asesor.
- **Puertos y kernels.** `arrancar` se detiene con un error si el puerto lo
  ocupa otro programa (casi siempre, el kernel del notebook 07), en lugar de
  usar en silencio el servidor viejo sin `consultar_tasa`.
- **Comprobar, no suponer.** El paso 10 revisa en la bitácora que cada pieza
  participó y que la respuesta trae las cifras de Python, porque las rutas las
  decide un LLM.
