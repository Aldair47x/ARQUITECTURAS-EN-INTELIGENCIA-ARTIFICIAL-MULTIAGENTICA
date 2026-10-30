# Resumen del Laboratorio 6

## Propósito

El notebook es un **caso resuelto** que continúa la sucursal bancaria ficticia
del laboratorio 5. Hasta ahora los agentes solo usaban **datos y cálculos**
(saldo, cuota); aquí se agrega un agente que responde con **documentos**: el
**Agente de Políticas** busca en el manual de la sucursal antes de responder.
Eso es **RAG** (*Retrieval-Augmented Generation*).

La pregunta de referencia es mixta: un cliente quiere una moto de $20.000.000,
pregunta por el aporte mínimo según la política, si le alcanza con su saldo
($5.000.000) y cuánto pagaría a 36 meses con un aporte de $5.000.000.

El notebook trae resuelto un **reto** sobre la Parte A: pasar de 4 archivos
`.md` en memoria a un manual de **6 PDFs** indexado en **FAISS** en disco, con
citas de **archivo y página**. El código original sigue comentado en las
celdas.

## Temas principales

### 1. La arquitectura: un Supervisor y tres agentes

| Agente | Herramienta | Fuente de la respuesta |
|---|---|---|
| 📚 Políticas | `buscar_en_manual` (RAG) | El manual de la sucursal |
| 💰 Cuentas | `consultar_saldo`, `consultar_movimientos` | Datos de la cuenta ficticia (Python) |
| 🧮 Créditos | `simular_cuota` | Cálculo de la anualidad (Python) |

El **Supervisor** no responde preguntas: decide a quién delegar y con qué tarea
concreta. Cada agente **vuelve** al Supervisor con su aporte, y al elegir
`finalizar` un nodo de **Respuesta** une los aportes conservando las citas.

### 2. Preparar el conocimiento (Parte A)

| Paso | Versión original (comentada) | Reto: PDF + FAISS |
|---|---|---|
| Manual | 4 `.md` cortos creados por el notebook | 6 PDFs en `manual_pdf/`: crédito vehicular, requisitos, seguros y tarifas, atención y reclamos, cuentas de ahorro y una circular de actualización |
| Cargar | Un `Document` por archivo | `PyPDFLoader`: un `Document` **por página**; se quita el encabezado que se repite en cada página |
| Metadatos | `fuente` | `fuente`, `pagina`, `codigo` y `vigente_desde` |
| Dividir | 300 caracteres, 50 de solapamiento | 800 y 120: las tablas del PDF salen con una celda por línea y con 300 una fila quedaría partida |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2`, 384 números | El mismo modelo, con vectores normalizados |
| Índice | `InMemoryVectorStore`, se recalcula en cada ejecución | `FAISS` guardado en `indice_faiss/`; se carga si la **huella** de los PDFs no cambió |
| Recuperar | `k=3`, *score* = similitud coseno | `k=3`, mismo *score* (producto interno de vectores normalizados), **más** la circular que modifique un documento recuperado (filtro por metadatos) |

Dos detalles de FAISS que cambian el resultado si se olvidan:

- **La medida de distancia.** Por defecto FAISS usa distancia L2, donde *más
  bajo* es más parecido. Con `DistanceStrategy.MAX_INNER_PRODUCT` y vectores
  normalizados, el *score* vuelve a ser la similitud coseno, donde *más alto*
  es más parecido. `save_local` no guarda esta opción, así que se pasa al crear
  y al cargar.
- **El pickle.** `index.pkl` se carga con `allow_dangerous_deserialization=True`:
  solo es seguro con un índice creado por uno mismo.

La prueba de recuperación muestra la idea central de los embeddings: la
pregunta dice «cuota inicial» y el manual dice «aporte mínimo». No comparten
palabras, pero sí significado, y la búsqueda encuentra el fragmento correcto.

### 3. RAG agéntico (Parte B)

La búsqueda no es un paso fijo antes del LLM: es una **herramienta** del agente.
El agente decide **cuándo** buscar y **qué** buscar, y puede buscar más de una
vez si la pregunta tiene varios temas (seguros y reclamos). La instrucción
clave es responder **solo** con los fragmentos, citar archivo y página entre
corchetes (`[01_Manual_Credito_Vehicular.pdf, p. 1]`; en la versión original,
`[credito_vehicular.md]`) y decir «El manual no tiene esa información» cuando no
la encuentra.

### 3b. Documentos que se contradicen

La circular `CIR-2026-07` modifica dos manuales: el aporte mínimo para motos
nuevas sube del 10 % al **15 %** y la sucursal cierra los sábados a las
**13:00** (antes a las 12:00). La búsqueda recupera las dos versiones, porque
el manual tiene más fragmentos sobre el tema y suele ganarle a la circular por
similitud. En una ejecución de prueba, con la consulta que redactó el agente,
la circular quedó fuera incluso con `k=4` y la respuesta usó el 10 % derogado.
Subir `k` no lo resuelve de forma confiable; por eso `buscar` lee de la propia
circular qué documentos modifica (`MODIFICADO_POR`) y, si recupera uno de
ellos, **adjunta** el fragmento más parecido de la circular con
`filter={'codigo': ...}`. Decidir cuál rige es trabajo del agente: cada
fragmento le llega con su fecha de vigencia y la instrucción le pide aplicar la
más reciente y citar ambas.

Cada especialista es un `create_agent` de LangChain: un pequeño grafo de
LangGraph (*LLM ⇄ herramientas*) con sus propias herramientas e instrucciones.

### 4. Controles

| Control | Qué evita |
|---|---|
| Contrato `Decision` (Pydantic, `Literal`) | Que el Supervisor elija un agente que no existe |
| `LIMITE_DECISIONES = 5` | Ciclos infinitos entre el Supervisor y los agentes |
| `recursion_limit=30` | Un recorrido demasiado largo del grafo |
| El agente recibe **solo su tarea** | Que un especialista trabaje con información que no le corresponde |
| `temperature=0` | Variación innecesaria entre ejecuciones |

### 5. Observar la colaboración

Cada participante deja un mensaje en la **bitácora** (quién le envió qué a
quién) y la herramienta RAG guarda los **fragmentos recuperados**. La interfaz
de Gradio dibuja un diagrama de secuencia con un carril por participante y una
tabla con los fragmentos, su fuente y su *score*. Se redibuja con
`sucursal.stream(..., stream_mode='updates')`, que avisa cada vez que termina
un nodo.

## Puntos clave a considerar

1. **El dato y el documento no se mezclan.** El saldo se consulta con una
   herramienta; la política, con RAG. Un saldo dentro del manual quedaría
   desactualizado.
2. **El embedding busca por significado, no por palabras.** «Cuota inicial»
   encuentra «aporte mínimo».
3. **La fuente viaja con el fragmento.** Los metadatos permiten citar, y la
   tabla de fragmentos permite comprobar que la cita es real.
4. **Fuera del manual no se improvisa.** Ante «¿Puedo pagar con
   criptomonedas?» el agente debe decir que el manual no tiene esa información.
5. **Los parámetros del RAG cambian el resultado.** Fragmentos muy pequeños
   pierden contexto; muy grandes mezclan temas. Con `k=1` una pregunta de dos
   temas puede quedar a medias.
6. **Un índice en disco necesita saber cuándo está viejo.** El índice guarda
   los vectores de los textos con los que se creó. La huella de los PDFs y de
   los parámetros decide si se carga o se reconstruye.
7. **La similitud no sabe de vigencias.** Los metadatos (qué documento
   modifica a cuál y desde cuándo) completan lo que el embedding no ve, y la
   fecha de vigencia permite que el agente elija la norma que rige.
8. **Limpiar el texto mejora la búsqueda.** El encabezado repetido en cada
   página haría parecerse a todos los fragmentos.

## Límites del ejemplo

Políticas, tasas y clientes son ficticios; el ejemplo no aprueba créditos. A
diferencia del laboratorio 5, la **respuesta final sí pasa por el LLM**, que une
los aportes de los agentes: puede reformular cifras o citas, así que conviene
contrastarla con la bitácora y con la tabla de fragmentos. El texto de los
PDFs se extrae con `pypdf`: sirve para PDFs con texto, no para documentos
escaneados (necesitarían OCR), y las tablas pierden su estructura de filas y
columnas. Las páginas se dividen por separado, así que una sección que cruza
de página queda en dos fragmentos.
