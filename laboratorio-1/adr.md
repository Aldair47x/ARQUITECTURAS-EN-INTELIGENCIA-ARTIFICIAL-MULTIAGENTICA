# ADR-001: Arquitectura multiagente con supervisor y escalamiento determinista para incidentes de pagos

- **Estado:** Aceptado
- **Fecha:** 2026-10-25
- **Autor:** Aldair Bernal Betancur
- **Evidencia:** [`01_RETO_Estudiante_Arquitectura_Pagos.ipynb`](./01_RETO_Estudiante_Arquitectura_Pagos.ipynb), ejecutado con Groq (`openai/gpt-oss-120b`, `temperature=0`)

## Contexto

Un sistema de pagos presenta 18 % de transacciones fallidas durante 25 minutos, sin evidencia confirmada de filtración y con mantenimiento en seis horas. Se necesita un plan para los próximos 30 minutos con riesgos y validaciones. Los requisitos que condicionan el diseño son:

1. No inventar causa raíz, filtración, acciones ejecutadas ni cifras.
2. Las acciones que puedan alterar pagos requieren **aprobación humana**; un error no es reversible como lo es reescribir un texto.
3. Debe poder auditarse quién propuso qué.

## Decisión

Se adopta un grafo secuencial de LangGraph con **tres especialistas, un supervisor y un punto de revisión humana**. La ruta tras el supervisor la decide una **regla determinista** (`requiere_aprobacion`), no el LLM.

```
START ─► Operaciones ─► Riesgos ─► Auditoría ─► Supervisor ─► ¿requiere_aprobacion(texto)?
                                                                 │ sí                │ no
                                                                 ▼                   ▼
                                                     Revisión humana (PENDIENTE)    END
                                                                 │
                                                                 ▼
                                                                END
```

- **Operaciones** propone medidas reversibles; **Riesgos** evalúa impacto y umbrales; **Auditoría** separa hechos de hipótesis y pide validaciones.
- **Supervisor** integra el plan con responsables por rol. Es el único que escribe `decision` y `requiere_revision`.
- **Revisión humana** es un marcador simulado: escribe `PENDIENTE` y nunca aprueba. Una aprobación real requeriría `interrupt()` y un checkpointer.
- Cada nodo escribe solo su campo y agrega su nombre a `bitacora`, que registra la ruta real.

## Alternativas consideradas

| Alternativa | Llamadas LLM | Latencia media (n = 3) | Ventajas | Inconvenientes |
|---|---|---|---|---|
| **A. Un solo agente (baseline)** | 1 | 3.77 s (desv. 0.58) | Más simple, rápida y barata | Sin trazabilidad por rol; sin separación explícita de hechos e hipótesis; el control depende del prompt |
| **B. Un especialista + supervisor** | 2 | 7.06 s (desv. 1.78) | Mismo control de escalamiento (3 de 3 ejecuciones a revisión humana) con la mitad de las llamadas | Sin evaluación de riesgos ni auditoría de hechos separadas |
| **C. Tres especialistas + supervisor (elegida)** | 4 | 21.38 s (desv. 1.01) | Trazabilidad por rol; la auditoría expone hechos, hipótesis y datos faltantes | ≈5.7× la latencia y 4× las llamadas del baseline; más complejidad |
| **D. Escalamiento decidido por el LLM** | igual que C | igual que C | Más flexible ante verbos no previstos | Un prompt no es una garantía: una respuesta mal formulada podría omitir la aprobación |

Se descartó D por el requisito 2: el control no debe depender de que el modelo lo recuerde. La paralelización de los especialistas no se evaluó; reduciría la latencia pero cambia el estado compartido (cada especialista dejaría de ver las propuestas previas).

## Justificación

Se elige C porque el criterio dominante es **control y trazabilidad**, y porque la auditoría produce una separación visible de hechos, hipótesis y datos faltantes que ni el baseline ni B generan de forma estructurada. La regla determinista cumple el requisito 2: en el caso de presión por una acción irreversible (D), el plan quedó retenido para revisión humana.

**Esta decisión no se apoya en una mejora de calidad demostrada.** La evidencia no compara la calidad del baseline con la del grafo, y B ofrece el mismo control a menor costo. C solo se justifica si el valor de la auditoría y de la evaluación de riesgos se confirma en una medición posterior.

## Consecuencias

**Positivas**

- Ruta auditable (`bitacora`) y propuestas separadas por rol.
- Escalamiento reproducible por una regla de código y probado con autocomprobaciones sin tokens.

**Negativas y riesgos observados**

- **Costo:** 4 llamadas y ≈21 s por incidente, además de más cuota por minuto y más piezas que mantener.
- **Textos cortados:** todas las respuestas de los agentes y las decisiones de los casos terminaron a mitad de frase por `max_tokens`, y el modelo no respetó los límites de palabras. La regla analiza texto incompleto.
- **Cifras inventadas:** aparecieron umbrales ausentes del escenario (`>5 %`, `>200 ms`, `25 %`, `80 %`). Pydantic valida forma, no verdad.
- **Escalamiento poco informativo:** los cuatro casos pasaron por revisión humana, porque la regla no distingue "solicitar aprobación para X" de "hacer X"; riesgo de fatiga de aprobaciones. Su comportamiento varió entre ejecuciones.
- **Falsos negativos de la regla:** verbos como "detener", "desconectar", "aislar" o "redirigir" no están en la lista.
- Con n = 3 no se pueden afirmar diferencias estadísticas de latencia ni de calidad.

## Acciones de seguimiento

1. Subir `max_tokens`, detectar truncamiento con `finish_reason` y salida estructurada del supervisor validada con `PropuestaEspecialista` o similar.
2. Validar por código que no aparezcan cifras ausentes del escenario.
3. Ampliar la lista de verbos de impacto y probar los falsos negativos.
4. Comparar la calidad de A, B y C con una rúbrica y más repeticiones, y revisar esta decisión con esos datos.
5. Implementar la aprobación real con `interrupt()`, checkpointer, registro de aprobador y tiempo máximo de espera (sesión 15).
