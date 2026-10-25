# Resumen del Laboratorio 2

## Propósito

El notebook es un **caso resuelto** de la sesión 2: no hay código por completar.
Muestra cómo convertir el marcador `PENDIENTE` del laboratorio 1 en una
aprobación humana real dentro del flujo. La idea central es que un agente puede
**proponer**, pero solo una **persona** puede **autorizar**, y esa autorización
debe ocurrir con una pausa real y reanudable.

El caso es una solicitud de reembolso ficticia: pedido `PED-1042`, producto
reportado como defectuoso, 5 días desde la entrega, valor de $450.000 COP y
**ninguna evidencia independiente** del defecto, solo el reporte del cliente.

## Temas principales

### 1. Elegibilidad frente a autorización

| Decisión | Quién la toma | Cómo |
|---|---|---|
| ¿Es elegible? | Python | `ruta_propuesta`: plazo de 15 días y recomendación del supervisor |
| ¿Se autoriza? | Una persona | `interrupt()` + `Command(resume=...)` |
| ¿Se registra? | Python | `ruta_decision` + comprobaciones en `registrar` |

La regla de la clase obliga a que **toda** propuesta elegible pase por una
persona, incluso bajo el umbral de $300.000 COP, para no confundir "cumple la
política" con "alguien lo aprobó".

### 2. Contratos Pydantic en cada frontera de confianza

- **`Analisis`** (atención y políticas): resumen, al menos una evidencia y al
  menos una incertidumbre. Obligar a declarar incertidumbres fuerza a reconocer
  que el defecto no está verificado.
- **`Propuesta`** (supervisor): solo `reembolsar` o `solicitar_informacion`; el
  supervisor **no puede** aprobar porque el contrato no tiene esa opción. El
  monto es un entero estricto ≥ 0.
- **`DecisionHumana`** (la persona): `aprobar` o `rechazar`, revisor y motivo.

`extra="forbid"` rechaza cualquier campo no declarado, por ejemplo un
`"autorizado": true` inventado por un LLM. Un contrato valida **forma**, no
**veracidad**.

### 3. Roles del equipo

- **Atención:** resume la solicitud con sus evidencias e incertidumbres.
- **Políticas:** contrasta el caso con la política, que recibe como dato
  explícito, y separa elegibilidad de autorización.
- **Supervisor:** prepara una propuesta, nunca una autorización.
- **Revisión humana:** pausa el grafo y presenta el caso a una persona; no llama
  al LLM.
- **Registro:** escribe el reembolso simulado solo tras la aprobación.
- **Cierre:** termina sin reembolso y deja escrito el motivo.

### 4. La pausa real: `interrupt()` y checkpointer

El grafo se compila con `checkpointer=InMemorySaver()`. Al llegar a
`revision_humana`, `interrupt(payload)` detiene la ejecución, guarda el estado y
devuelve el payload a quien llamó `invoke`. La solicitud se reanuda con
`app.invoke(Command(resume=respuesta), config)` usando el **mismo** `thread_id`.
`app.get_state(config)` permite inspeccionar dónde quedó esperando.

### 5. Re-ejecución al reanudar

Al reanudar, `revision_humana` vuelve a ejecutarse **desde la primera línea**; la
segunda vez `interrupt()` no pausa, sino que devuelve la respuesta de la persona.
El notebook lo hace visible con un contador que termina en 2. Por eso no deben
ponerse llamadas al LLM, cobros ni escrituras antes de `interrupt()` en el mismo
nodo.

### 6. Guardrails y defensa en profundidad

- **Monto exacto:** si el supervisor recomienda reembolsar con un monto distinto
  al del pedido, `verificar_monto` detiene el flujo con error.
- **Re-verificación antes del efecto:** `registrar` vuelve a comprobar decisión,
  recomendación y monto aunque la ruta ya los haya filtrado.
- **Idempotencia local:** `REGISTRO.setdefault` evita dos reembolsos del mismo
  pedido dentro del proceso.
- **Controles con `raise`, no con `assert`:** Python ignora los `assert` con
  optimizaciones (`-O`).

### 7. Pruebas del control

Nueve pruebas automáticas, cada una con su propio `thread_id`: espera sin
respuesta, aprobación, idempotencia, rechazo, separación de hilos, respuesta
humana inválida, caso fuera de plazo, guardrail de monto y solicitud de
información. Prueban el **control** con decisiones de ejemplo; no evalúan la
calidad de un LLM real.

## Puntos clave a considerar

1. **Proponer no es autorizar.** El supervisor recomienda; la autorización es de
   una persona y ocurre en otro nodo.
2. **`interrupt()` no es `PENDIENTE`.** `PENDIENTE` termina el flujo sin
   decisión; `interrupt()` guarda una ejecución que continúa donde se quedó.
3. **La aprobación nunca es el valor por defecto.** `DECISION` empieza en `None`
   para que ejecutar todo sin leer no decida el caso.
4. **El código antes de `interrupt()` se repite.** Los efectos van en nodos
   posteriores a la aprobación.
5. **El `thread_id` es la llave de cada solicitud.** Reanudar con otro `config`
   no continúa el caso, y una solicitud se reanuda una sola vez.
6. **`InMemorySaver` no es durable.** Si se reinicia el kernel o Colab, los casos
   pausados se pierden.
7. **La identidad del revisor es declarada, no autenticada.**

## Límites del ejemplo

Registro y checkpoints en memoria, identidad del revisor sin autenticación, sin
pagos reales y sin persistencia entre reinicios. La idempotencia es por pedido y
dentro de un proceso: no garantiza ejecución exactamente una vez en un sistema
distribuido. Si la propuesta cambia después de aprobarla, debe pedirse una nueva
autorización. Las pruebas simuladas no evalúan respuestas reales de Groq.

## Transferencia al reto de pagos

El paso 11 propone llevar el mecanismo al notebook 01 en una **copia de
evolución**, sin tocar la entrega: sustituir `PENDIENTE` por un nodo con
`interrupt()` que presente incidente, plan, riesgos y auditoría; compilar con
checkpointer y un `thread_id` por incidente; y verificar las rutas de espera,
aprobación y rechazo sin ejecutar acciones reales. Preguntas de cierre: quién
puede aprobar y cómo se verifica su identidad, qué propuesta exacta se aprobó,
qué código se repite al reanudar y qué sigue sin garantizar Pydantic.
