# Ejercicio · La oficina del anteproyecto multiagente

**Versión alterna del laboratorio 5 · Router, supervisor y jerarquía**

Notebook: [`05b_Oficina_Anteproyecto_CacaoIA.ipynb`](./05b_Oficina_Anteproyecto_CacaoIA.ipynb)

## Contexto

El laboratorio 5 compara tres arquitecturas multiagente en una sucursal bancaria
ficticia. Esta versión alterna aplica la misma comparación a un problema propio:
un equipo de agentes que **revisa un anteproyecto de maestría** antes de
enviarlo al director de tesis.

La organización se basa en **cacaoia-utp**, un entorno multiagente construido
sobre Claude Code para redactar un anteproyecto. En ese entorno, un
`orquestador-tesis` decide qué especialista invocar; los auditores
(`verificador-citas`, `auditor-coherencia`, `auditor-metodologico`,
`critico-viabilidad` y `jurado-simulado`) solo emiten informes y no editan el
documento; y unos scripts deterministas hacen los chequeos mecánicos. El
notebook conserva esa organización, pero **todos los datos son ficticios**:
el anteproyecto `AP-DEMO`, sus citas, sus objetivos y sus cifras.

| Área | Especialistas | Qué calcula la herramienta (Python) |
|---|---|---|
| Documento | Citas, Coherencia | Citas sin entrada o sin ficha; objetivos sin actividades y actividades sin semanas |
| Diseño | Metodología, Viabilidad | Baseline, métrica y variable respuesta; entrenamiento máximo, horas de cómputo y páginas |

Cada hallazgo tiene una severidad: **BLOQUEANTE** (impide enviar el documento),
**GRAVE** o **AVISO**. Ningún agente aprueba el anteproyecto: eso lo decide el
director de tesis.

## Objetivos de aprendizaje

1. Predecir y luego medir **quién decide**, **cuántas veces** y **quién recibe
   los resultados** en cada arquitectura.
2. Distinguir lo que decide el LLM (rutas y explicaciones) de lo que calcula
   Python (hallazgos y cifras).
3. Evaluar cuánto cuesta **cambiar la organización** (agregar un especialista)
   en cada arquitectura.
4. Justificar una decisión de arquitectura con evidencia, en un ADR.

## Antes de empezar

Ejecuta los pasos 0 a 14 del notebook y deja la interfaz abierta. Usa los
controles por defecto (50 muestras, 5 pliegues, 14 páginas, 90 horas de cómputo
y 120 disponibles) salvo que el ejercicio diga otra cosa.

---

## Parte 1 · Predecir (antes de ejecutar)

Para la solicitud **«Prepara la entrega: revisa citas, coherencia, metodología y
viabilidad»**, completa la tabla **sin ejecutar nada**:

| Pregunta | Router | Supervisor | Jerárquica |
|---|---|---|---|
| ¿Cuántas decisiones de ruta toma un LLM? | | | |
| ¿Cuántos mensajes tendrá la bitácora? | | | |
| ¿En qué orden actuarán los especialistas? ¿Es fijo? | | | |
| ¿Cuántas llamadas a Groq en total? | | | |
| ¿Cambian los hallazgos? | | | |

> Pista: además de las decisiones de ruta, cuenta la llamada de Recepción y la
> explicación que escribe cada especialista. El Router no usa LLM para decidir.

## Parte 2 · Ejecutar y registrar la traza

1. Ejecuta la solicitud de la parte 1 en las **tres** arquitecturas.
2. Para cada una, registra la traza de la tabla «Mensajes entre participantes»:

   | Paso | Emisor | Destinatario | Mensaje (resumido) |
   |---|---|---|---|
   | | | | |

3. Compara con tu predicción. ¿En qué te equivocaste y por qué?
4. Ejecuta **dos veces** la arquitectura Supervisor. ¿Cambió el orden de los
   especialistas? ¿Cambiaron los hallazgos? Explica por qué uno puede variar y
   el otro no.

## Parte 3 · Cambiar un parámetro

El diseño ficticio promete comparar tamaños de entrenamiento de 20, 40 y 60
muestras. Con k pliegues, cada modelo entrena con ⌊n·(k − 1)/k⌋ muestras.

1. Con los valores por defecto, ¿qué hallazgo reporta el Crítico de viabilidad?
2. Cambia **Muestras** a 75 y repite «¿El diseño se puede ejecutar con las
   muestras que tenemos?». ¿Qué cambió en la respuesta?
3. Calcula a mano el **mínimo** de muestras que hace viable el tamaño 60 con 5
   pliegues y con 10 pliegues. Compruébalo en la interfaz.
4. Cambiar un número, ¿hace que alguna arquitectura tome decisiones distintas?
   ¿Por qué?

## Parte 4 · Agregar un quinto especialista: `jurado-simulado`

En cacaoia-utp, `jurado-simulado` simula la sustentación ante el comité y
**recibe el informe del crítico de viabilidad**: su trabajo es convertir los
hallazgos en las preguntas que los proponentes tendrán que responder.

1. Escribe su herramienta en Python: por cada hallazgo BLOQUEANTE o GRAVE de
   las demás revisiones, una pregunta probable de sustentación.
2. Decide dónde va en la organización: ¿en el área de Diseño, en una nueva área
   de Defensa o en otra parte? Justifícalo.
3. Para cada arquitectura, anota **qué partes del código** tuviste que cambiar
   (por ejemplo `AREAS`, `NOMBRES`, el contrato `Objetivos`, el rol de
   Recepción, `herramienta`, `router` o `crear_grafo`).
4. El jurado necesita que las otras revisiones ya hayan terminado. ¿Qué
   arquitectura lo garantiza por construcción? ¿En cuál depende de lo que elija
   el LLM? Si depende del LLM, agrega un **control en Python** que lo impida
   (pista: las opciones permitidas de `elegir_siguiente`).

## Parte 5 · ADR breve (máximo una página)

Escribe un ADR que responda: **¿qué arquitectura usarías para la oficina del
anteproyecto y por qué?** Usa la evidencia de las partes 2 a 4, no
suposiciones.

```
# ADR-xxx: <título>
- Estado: Propuesto
- Contexto: el problema y las restricciones (control, costo en llamadas, trazabilidad).
- Decisión: la arquitectura elegida.
- Alternativas consideradas: las otras dos (y la del reto, si la hiciste), con su
  ventaja y su costo.
- Consecuencias: qué se gana, qué se pierde y qué riesgo queda abierto.
- Evidencia: cifras de tus trazas (mensajes, decisiones, llamadas).
```

Incluye una respuesta corta a esta pregunta: **¿cuál de las tres describe mejor
cómo funciona hoy cacaoia-utp?** Pista: el orquestador decide según lo que se
tocó, pero la revisión completa corre los auditores en un orden fijo.

---

## Reto · Una cuarta arquitectura: secuencial con paradas

La revisión completa de cacaoia-utp (`/revisar-anteproyecto --completa`) no la
decide un LLM: corre los auditores **en un orden fijo** y **se detiene** en
cuanto aparece un bloqueante, porque no tiene sentido auditar la metodología de
un documento cuya bibliografía ni siquiera cuadra.

1. Implementa `crear_grafo('Secuencial')` con el orden citas → metodología →
   coherencia → viabilidad. Después de cada especialista, una arista condicional
   en Python decide si se continúa o se salta a `respuesta`.
2. Con los valores por defecto, ¿dónde se detiene? ¿Cuántas llamadas a Groq
   hace frente a las otras tres arquitecturas?
3. ¿Qué información pierden los proponentes cuando el flujo se detiene pronto?
   ¿Cuándo compensa?
4. Agrégala como cuarta opción en la interfaz y en tu ADR.

## Entregables

- [ ] Tabla de predicciones (parte 1) y trazas de las tres arquitecturas (parte 2)
- [ ] Respuestas de la parte 3, con el mínimo de muestras calculado y comprobado
- [ ] Código del quinto especialista y lista de cambios por arquitectura (parte 4)
- [ ] ADR de máximo una página (parte 5)
- [ ] Opcional: la arquitectura secuencial con paradas (reto)
- [ ] La clave de Groq **no** aparece en el notebook ni en las capturas
