V# **Actividad · Diseña e implementa “ViajaFácil”**

**Arquitecturas multiagénticas · Trabajo individual · 90 minutos (Parte A: 30 min · Parte B: 60 min) · Socialización: hoy a las 8:00 p. m.**  
ViajaFácil es una agencia de viajes ficticia que quiere un asistente con IA. Un cliente escribe:  
*“Quiero ir a Cartagena 4 días en diciembre con mi pareja, presupuesto de 3 millones. ¿Qué me recomiendas?”*  
El asistente debe poder:

> 1. Buscar vuelos y hoteles disponibles con sus precios. Hay un sistema de reservas que ya existe.  
> 2. Responder preguntas sobre las políticas de la agencia, que están en un manual de 50 páginas: cancelaciones, equipaje, reembolsos.  
> 3. Armar una propuesta combinando vuelos, hotel y presupuesto.  
> 4. Revisar que el total no supere el presupuesto del cliente.  
> 5. Hacer la reserva, pero **solo si el cliente lo aprueba**.  
> 6. Pedir el clima a un **agente de otra empresa** que ya existe y que ViajaFácil no controla.

## **Parte A · Diseña en papel (30 min)**

**1\. Agentes.** Lista los agentes de tu sistema en una tabla:

| Agente | Qué hace | Qué NO hace |
| :---- | :---- | :---- |
|   |   |   |
|   |   |   |

**2\. Clasifica cada capacidad (1 a 6).** ¿Es una herramienta (función), RAG (consulta a documentos), otro agente, MCP o A2A? Justifica con una frase cada una.  
**3\. Arquitectura.** Elige un patrón: secuencial, paralelo, router, supervisor o jerárquica. Justifica en 2 frases por qué ese y no otro.  
**4\. ¿Qué ve cada agente?** ¿Quién necesita ver el presupuesto? ¿Quién los datos de pago? ¿Por qué no todos deberían ver todo?  
**5\. Humano en el bucle.** ¿En qué paso exacto debe aprobar una persona? ¿Qué pasa si la rechaza?  
**6\. Diagrama.** Dibuja tu arquitectura con flechas. Usa un color para MCP, otro para A2A y otro para RAG.

## **Parte B · Impleméntalo reutilizando código del curso (60 min)**

**Notebook:** [07b\_Reto\_ViajaFacil\_v2.ipynb](https://colab.research.google.com/drive/1BWnPQiKXbv5d11T7hDrohH5k6eUWaRPo)  
Ábrelo y haz **Archivo → Guardar una copia en Drive**. Trabaja sobre tu copia.  
El notebook ya trae los datos, las herramientas, un contador de llamadas al LLM y la interfaz de Gradio. Tú completas **7 huecos** (\_\_\_) copiando patrones de los notebooks **06** (MCP y A2A) y **06a** (multiagente con RAG):

| Paso | Qué completas | Lo copias de… |
| :---- | :---- | :---- |
| 2 | Los agentes de Políticas y Clima con create\_agent (huecos 1, 2 y 3\) | Notebook 06: crear\_agente\_creditos() · notebook 06a: crear\_especialista() |
| 3 | Los agentes envueltos como herramientas del Coordinador (huecos 4 y 5\) | Notebook 06: consultar\_agente\_creditos (paso 9\) |
| 4 | Las herramientas del Coordinador (hueco 6\) | Notebook 06: crear\_asesor() (paso 10\) |
| 5 | La aprobación humana antes de reservar (hueco 7\) | Notebook de Reembolsos (humano en el bucle) |

Cada paso del notebook dice cuál es la **salida esperada**. Al final abre Gradio y mira el diagrama y cuántas llamadas al LLM hizo tu sistema.  
🔑 Necesitas tu GROQ\_API\_KEY en Secrets de Colab. Todos los datos son ficticios.

## **Pistas**

> * Lo que solo informa o calcula es una **herramienta**.  
> * Lo que razona y decide es un **agente**.  
> * Lo que está en documentos largos se resuelve con **RAG**.  
> * Lo que se comparte con otros sistemas usa **MCP** (herramientas) o **A2A** (agentes).  
> * Si una celda da error, revisa el hueco de esa celda y compáralo con el notebook 06\.

## **Entrega y socialización**

> * **Entrega:** foto o captura del diagrama (Parte A) \+ el enlace a tu copia del notebook con los 7 huecos completos y ejecutado (Parte B).  
> * **Hoy a las 8:00 p. m.** nos conectamos para compartir lo realizado. Prepara en 2 minutos:  
  1. Tu diagrama y por qué elegiste esa arquitectura.  
  2. Una captura de Gradio con la pregunta principal: diagrama y número de llamadas al LLM.  
  3. ¿Cómo reducirías esas llamadas? (Pista: ¿el Agente Clima necesita ser un agente?)

**Reto opcional:** convierte al Agente Clima en una herramienta simple (dale consultar\_clima directo al Coordinador) y compara cuántas llamadas al LLM se ahorran.