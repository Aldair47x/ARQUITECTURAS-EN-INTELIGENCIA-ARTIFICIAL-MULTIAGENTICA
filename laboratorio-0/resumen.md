# Resumen del Laboratorio 0

## Propósito

El notebook presenta una demostración guiada de un equipo editorial
multiagente. Su objetivo es comprender cómo se coordinan varios agentes antes
de diseñar una solución propia; no constituye por sí mismo la entrega
evaluada.

El caso consiste en crear una entrada de blog breve sobre cómo los pequeños
negocios pueden usar IA de forma responsable.

## Temas principales

### 1. Requisitos y arquitectura

El artículo debe tener título y cuerpo de máximo 130 palabras, tono claro,
sin cifras o beneficios inventados, sin fuentes no verificadas y con una
advertencia breve sobre privacidad. La arquitectura exige revisiones SEO, legal
y ética, consolidación de hallazgos y una decisión final de aceptación o
reescritura.

La lección central es distinguir entre:

- requisitos que un agente intenta cumplir mediante su rol y prompt;
- garantías que dependen de la arquitectura, las rutas, los límites y las
  validaciones.

### 2. Estado compartido

El estado es el tablero común del equipo. Los nodos leen información existente y
escriben resultados para que los siguientes agentes puedan continuar el flujo.
Entre los datos relevantes están el tema, el borrador, las revisiones
especializadas, los hallazgos consolidados, la decisión, el número de versión y
las métricas de ejecución.

Cada agente debe tener una responsabilidad clara y modificar únicamente la
parte del estado que le corresponde.

### 3. Roles del equipo editorial

- **Escritor:** redacta el borrador y puede reescribirlo usando el feedback
  consolidado.
- **Revisor SEO:** revisa claridad, estructura, título y aspectos relacionados
  con buscabilidad.
- **Revisor legal:** busca afirmaciones riesgosas, cifras inventadas, fuentes no
  verificadas y problemas de cumplimiento.
- **Revisor ético:** revisa sesgos, impactos, uso responsable y advertencias de
  privacidad.
- **Metarrevisor:** consolida los hallazgos de los revisores sin duplicarlos.
- **Evaluador:** decide si el resultado se acepta o debe reescribirse.

La especialización aporta perspectivas distintas, pero también aumenta las
llamadas al modelo y la necesidad de coordinación.

### 4. Interfaz con el modelo

El notebook utiliza un único punto de contacto con Groq. Esto centraliza la
configuración del modelo, la clave, los parámetros y el registro de llamadas.
También incluye un modo simulado para probar la lógica del grafo sin consumir
tokens.

### 5. LangGraph como orquestador

El flujo se modela como un `StateGraph` con:

- estado compartido;
- nodos que representan agentes;
- aristas fijas para la secuencia de revisiones;
- una arista condicional para decidir entre publicar o reescribir;
- `START` y `END` como puntos de entrada y salida.

La arquitectura evita que la coordinación dependa únicamente de instrucciones
en lenguaje natural.

### 6. Ejecución y evidencia

El notebook muestra cómo ejecutar el grafo completo, inspeccionar la respuesta
de cada agente, medir llamadas y latencia por nodo y observar la ejecución paso
por paso mediante `stream()`.

Estas métricas permiten analizar el costo de coordinación, no solo la calidad
del texto producido.

## Puntos clave a considerar

1. **Un prompt no es una garantía.** La ausencia de cifras inventadas o fuentes
   no verificadas requiere validaciones externas, reglas automáticas o revisión
   humana.
2. **La arquitectura también controla requisitos.** Las aristas, los límites y
   la ruta condicional pueden impedir flujos incompletos o bucles infinitos.
3. **El número de llamadas importa.** Si el evaluador revisa después de que el
   escritor incorpora feedback, se valida mejor la versión final, pero aumentan
   llamadas, latencia y costo.
4. **Debe existir un límite de versiones.** El caso usa un máximo de tres
   versiones para evitar reescrituras indefinidas.
5. **La especialización no equivale automáticamente a coordinación útil.** Un
   sistema multiagente debe justificar qué valor aporta cada rol.
6. **El modo simulado es útil para depurar.** Permite probar rutas y contratos
   antes de realizar llamadas reales a Groq.
7. **Las claves deben permanecer fuera del código.** `.env` se carga con
   `python-dotenv` y está excluido por `.gitignore`.

## Límites del ejemplo

Este notebook es una referencia educativa. No demuestra por sí solo que un
equipo multiagente sea mejor que un agente único, que las fuentes hayan sido
verificadas externamente o que el texto sea adecuado para publicación sin
revisión humana.

## Transferencia a un nuevo proyecto

Para crear otro laboratorio se debe elegir un problema distinto, justificar
por qué necesita varios agentes, describir qué información lee y escribe cada
uno, incluir una decisión de coordinación, medir llamadas y latencia, y probar
casos como información insuficiente o contradicción entre agentes.
