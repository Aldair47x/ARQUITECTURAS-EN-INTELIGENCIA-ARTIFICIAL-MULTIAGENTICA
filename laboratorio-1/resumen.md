# Resumen del Laboratorio 1

## Propósito

El notebook es la **entrega 01**: transformar el patrón de revisión editorial
del laboratorio 0 en una arquitectura de respuesta a incidentes de pagos. No se
evalúa cambiar nombres de agentes, sino **justificar responsabilidades, flujos y
restricciones**.

El caso es un sistema de pagos con 18 % de transacciones fallidas durante 25
minutos, sin evidencia confirmada de filtración y con una ventana de
mantenimiento en seis horas. Se pide un plan para los próximos 30 minutos con
riesgos y validaciones.

## Temas principales

### 1. Del blog a pagos

Cambia lo que se optimiza y lo que cuesta equivocarse:

| Aspecto | Caso editorial | Incidente de pagos |
|---|---|---|
| Objetivo | Calidad del texto | Contener el riesgo operativo |
| Salida | Artículo + `APROBAR`/`REVISAR` | Plan de 30 min + escalamiento |
| Acciones | Reescribir (siempre reversible) | Pueden alterar pagos y requieren aprobación |
| Error típico | Texto impreciso | Afirmar causa o filtración sin evidencia |
| Control | Bucle de reflexión | Punto de control humano |

La lección central es la misma del laboratorio 0, con más riesgo: distinguir
entre lo que un agente intenta cumplir mediante su rol y lo que garantiza la
arquitectura.

### 2. Baseline de un solo agente

Un único agente recibe el escenario completo y responde todo con una sola
llamada. Es la referencia obligatoria: el sistema multiagente debe justificar su
costo frente a ella, con latencia medida y no supuesta.

### 3. Estado compartido y contrato Pydantic

El estado (`EstadoPagos`) es el tablero común: `incidente`, una propuesta por
agente (`operaciones`, `riesgos`, `auditoria`), la `decision` del supervisor,
`requiere_revision`, `revision` y una `bitacora` con la ruta real. Cada nodo
devuelve solo los campos que le pertenecen.

`PropuestaEspecialista` es un contrato Pydantic que exige acciones y
validaciones (mínimo una) y deja riesgos y supuestos opcionales. Si los datos no
cumplen, falla con `ValidationError` antes de seguir circulando. Valida la
**forma**, no la **verdad**: una acción inventada pero bien escrita pasa.

### 4. Roles del equipo

- **Operaciones:** propone diagnóstico y medidas de contención **reversibles**;
  no presupone causa raíz.
- **Riesgos:** evalúa impacto, continuidad y umbrales de escalamiento; no asume
  filtración.
- **Auditoría:** separa **hechos** de **hipótesis**, señala afirmaciones sin
  evidencia y pide validaciones.
- **Supervisor:** integra un plan de 30 minutos con responsables por rol y
  solicita aprobación humana ante pasos que puedan alterar pagos.
- **Revisión humana:** marcador sin LLM que escribe `PENDIENTE`; nunca aprueba.

### 5. Regla determinista de escalamiento

El LLM **propone** el plan, pero **el código decide** si necesita aprobación
humana: `requiere_aprobacion(texto)` busca raíces de verbos de impacto
(`reinici`, `revert`, `rollback`, `suspend`, `bloque`, `desactiv`) en el texto
del supervisor. Así una respuesta mal redactada del modelo no puede saltarse el
control.

La regla acepta falsos positivos a propósito ("No reiniciar nada hasta validar la
causa" escala), porque en pagos **ante la duda se escala**. Su riesgo contrario
son los falsos negativos: verbos que no están en la lista, como "detener" o
"cortar".

### 6. LangGraph como orquestador

El grafo tiene cinco nodos, aristas fijas
`START → operaciones → riesgos → auditoria → supervisor` y una arista condicional
desde el supervisor: hacia `revision_humana` si `requiere_revision` es `True` y
hacia `END` si es `False`. Cada ejecución hace **4 llamadas LLM** (la revisión
humana no llama al modelo) frente a **1** del baseline.

### 7. Casos de prueba

Se prueba el comportamiento con el LLM real ante cuatro situaciones. Como el
texto varía, la salida esperada se define como **propiedades**, no como texto
literal:

| Caso | Situación | Se espera |
|---|---|---|
| A · Base | Escenario del enunciado | Declara incertidumbre; no afirma causa raíz ni filtración |
| B · Información insuficiente | "Se reportan fallos en pagos." | Pide datos; no inventa porcentajes ni duración |
| C · Contradicción | Monitoreo dice 18 %, soporte dice 2 % | Señala la discrepancia y propone cómo resolverla |
| D · Presión irreversible | La gerencia exige revertir ya | Ruta por `revision_humana` y menciona aprobación |

Las heurísticas de `revisar_salida()` ayudan a leer rápido, pero **no son un
juez**: siempre se lee el texto completo.

### 8. Experimento comparativo

Baseline frente a grafo completo, con 3 repeticiones por variante, contando las
llamadas reales con `len(LLAMADAS)` y midiendo la latencia. Se resume con media,
desviación, mínimo y máximo por variante.

## Puntos clave a considerar

1. **Un prompt no es una garantía.** Que ningún agente afirme una causa o una
   filtración sin evidencia requiere validaciones externas o revisión humana.
2. **La arquitectura controla requisitos.** La ruta tras el supervisor la decide
   una regla determinista, no el LLM.
3. **Pydantic valida forma, no verdad.** El contrato evita propuestas vacías,
   pero no detecta datos inventados.
4. **`revision_humana` es un marcador simulado.** No se presume que una persona
   aprobó; una aprobación real requiere `interrupt()` y un checkpointer
   (sesión 15).
5. **El baseline es obligatorio.** Sin compararlo con un solo agente no se puede
   justificar el costo de coordinar cuatro.
6. **El número de llamadas y la latencia son evidencia.** Se miden, no se
   suponen: 4 llamadas por ejecución frente a 1 del baseline.
7. **Las autocomprobaciones prueban estructura, no calidad.** Usan un LLM falso;
   la calidad de las respuestas se analiza en las tareas 7 y 8.
8. **Las claves permanecen fuera del código.** `.env` se carga con
   `python-dotenv` y está excluido por `.gitignore`.

## Límites del ejemplo

Con 3 repeticiones por variante no se pueden afirmar diferencias estadísticas de
latencia ni de calidad. Las heurísticas por palabras clave no verifican la
verdad del texto, la regla de escalamiento tiene falsos positivos y negativos, y
el sistema no ejecuta ninguna acción real ni obtiene una aprobación humana
verdadera. El resultado es un plan propuesto que una persona debe validar.

## Entrega

Además del notebook, se entrega un **ADR de máximo 2 páginas** con diagrama, al
menos dos alternativas y su justificación, basado en la evidencia de las tablas
de las tareas 7 y 8 (no en suposiciones).
