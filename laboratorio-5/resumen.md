# Resumen del Laboratorio 5

## Propósito

El notebook es un **caso resuelto** de la sesión 3. Compara tres formas de
organizar un equipo de agentes manteniendo fijo todo lo demás: el mismo cliente
ficticio, las mismas herramientas y la misma respuesta final. Lo único que
cambia es **quién decide a quién llamar**, **cuándo decide** y **quién recibe
los resultados**.

El caso es un cliente ficticio (`DEMO-001`, saldo de $5.000.000 COP) que
pregunta por sus ahorros y quiere simular la financiación de una moto de
$20.000.000 con un aporte de $5.000.000 a 36 meses, con una tasa didáctica del
1 % mensual, ingresos de $3.500.000 y obligaciones de $700.000.

## Temas principales

### 1. La organización compartida

Dos áreas con dos especialistas cada una, definidas en un solo diccionario
(`AREAS`) que usan las tres arquitecturas:

| Área | Especialistas | Herramienta (Python) |
|---|---|---|
| Cuentas | Saldos, Movimientos | Lee la cuenta ficticia |
| Créditos | Simulación, Requisitos | Calcula la cuota y un límite ilustrativo |

Las tres comparten el inicio (**Recepción**, que interpreta la solicitud) y el
final (**Respuesta**, que arma el texto con los números de las herramientas).

### 2. Router: decide una sola vez

El Router mira los objetivos al inicio y elige `cuentas`, `creditos`, `ambas` o
`ninguna`. No usa LLM. Después cada área ejecuta a sus especialistas en orden y
**nadie revisa** entre uno y otro. Es la arquitectura más barata y predecible,
pero no puede corregir el rumbo.

### 3. Supervisor: decide después de cada resultado

El Supervisor conoce a los cuatro especialistas. Cada especialista **le
devuelve** el resultado y él decide el siguiente paso o `finalizar`. Lo que lo
define son las aristas de retorno (`add_edge('saldos', 'supervisor')`, etc.).
Con tres tareas toma cuatro decisiones: la última es `finalizar`.

### 4. Jerárquica: Director y coordinadores

Dos niveles de decisión. El **Director** solo conoce áreas y delega en un
equipo; cada **Coordinador** solo conoce a sus especialistas. Cada equipo es un
**subgrafo**: un `StateGraph` compilado que se agrega como un nodo más del grafo
principal. Hay más pasos y más llamadas, pero el resultado es el mismo.

| | Router | Supervisor | Jerárquica |
|---|---|---|---|
| ¿Quién elige el trabajo? | Router (áreas) | Supervisor (especialistas) | Director (áreas) y coordinadores (especialistas) |
| ¿Cuándo decide? | Una vez, al inicio | Después de cada resultado | En cada nivel, al recibir resultados |
| ¿Quién recibe los resultados? | El área y luego Respuesta | El Supervisor | El coordinador y luego el Director |

### 5. El LLM decide, Python calcula

| Pieza | La hace |
|---|---|
| Entender la solicitud | LLM, con el contrato `Objetivos` |
| Elegir el siguiente paso | LLM, con el contrato `Seleccion` y solo entre opciones permitidas |
| Saldo, cuota y límite | Python |
| Explicar cada resultado | LLM, en un texto corto |
| Respuesta final | Python, a partir de los resultados |

Controles que evitan que el LLM se salga del guion: los contratos Pydantic, la
lista de **opciones permitidas** (si el LLM elige otra cosa, el flujo se
detiene), un **límite de 6 decisiones** y el `recursion_limit` del grafo. Los
importes vienen de los controles numéricos, no del texto de la solicitud.

### 6. Observar la coordinación

Cada nodo deja un mensaje en la **bitácora** (quién le habló a quién y con qué
datos). La función `observable` envía avisos de inicio y fin con
`get_stream_writer()`, y la interfaz de Gradio los recibe con
`stream(..., stream_mode='custom', subgraphs=True)` para pintar en vivo qué
participante está trabajando, incluidos los coordinadores dentro de los
subgrafos.

### 7. Anexo: las tres arquitecturas escritas a mano

El anexo reconstruye cada arquitectura sin fábricas de nodos, sin ciclos `for`
y sin Gradio, con cada `add_node` y `add_edge` explícito y un `print` en cada
nodo. Sirve para ver que `crear_grafo()` produce exactamente la misma
estructura.

## Puntos clave a considerar

1. **La arquitectura cambia el recorrido, no el resultado.** Con los mismos
   datos, las tres llegan al mismo saldo, cuota ($498.215) y límite ($525.000).
2. **Más niveles de decisión implican más llamadas y más latencia.** Para «¿Cuánto
   saldo tengo?» la Jerárquica necesita el triple de llamadas que el Router.
3. **El orden de los especialistas puede variar** entre ejecuciones porque decide
   un LLM; los números no, porque los calcula Python.
4. **Las opciones permitidas acotan al LLM.** No puede inventar especialistas ni
   áreas: si elige algo fuera de la lista, el flujo se detiene.
5. **Fuera de alcance no se improvisa.** Ante «Quiero abrir un seguro de viaje»
   el sistema pide reformular en lugar de crear un equipo nuevo.
6. **La respuesta final no pasa por el LLM,** así que no puede alterar las cifras.
7. **La clave nunca va en el código**, y en local la interfaz no se publica con
   un enlace público.

## Límites del ejemplo

Datos, tasa y política son ficticios; no hay aprobación de créditos ni
movimientos de dinero. Las explicaciones de cada especialista las escribe el
LLM y pueden añadir juicios que no están en los datos: en una ejecución local,
el especialista de Saldos escribió que el saldo "es insuficiente para aprobar
un crédito", a pesar de la instrucción de no aprobar créditos. Esas
explicaciones aparecen en la bitácora, no en la respuesta final, que se arma
con Python.

## Versión alterna: la oficina del anteproyecto

`05b_Oficina_Anteproyecto_CacaoIA.ipynb` aplica la misma comparación a un
problema propio: un equipo que revisa un anteproyecto de maestría ficticio
(`AP-DEMO`) antes de enviarlo al director. La organización viene de
cacaoia-utp:

- un **orquestador** que decide qué especialista invocar (Supervisor y Director);
- **auditores que no editan**, solo emiten informes, repartidos en el área de
  Documento (citas, coherencia) y la de Diseño (metodología, viabilidad);
- **chequeos deterministas** en Python que producen los hallazgos con su
  severidad (BLOQUEANTE, GRAVE, AVISO).

El cálculo central del área de Diseño es el **entrenamiento máximo con
validación cruzada**, ⌊n·(k − 1)/k⌋: con 50 muestras y 5 pliegues es 40, así que
un diseño que promete entrenar con 60 muestras no se puede ejecutar. El
ejercicio (`05b_Ejercicio_Oficina_Anteproyecto.md`) agrega dos preguntas que el
banco no tenía: cuánto cuesta en cada arquitectura **sumar un especialista que
depende de otros** (`jurado-simulado`) y, como reto, la cuarta arquitectura que
usa cacaoia-utp en su revisión completa, **secuencial con paradas**, donde el
flujo se detiene ante el primer bloqueante.

## Ejercicio de clase

El ejercicio está en `05_Ejercicio_Sucursal_Bancaria.docx`: predecir, ejecutar,
registrar la traza de una consulta mixta en las tres arquitecturas, probar un
aporte de $6.000.000 (que ya no cabe en el saldo ficticio de $5.000.000) y
escribir un ADR breve.
