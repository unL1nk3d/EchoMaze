# RAW DEF 

porfavor implementa en el sistema de scoring el siguiente algoritmo: definicion del algoritmo
basada en termodinamica

el ruido se define como 

-log_2(P(evento))

donde P es la probabilidad y
evento es cada entrada captada en un historial o log de acciones
realizadas por el usuario

### pasos de aplicacion  del algorimo 

1) buscar con cheatIngestor el comando emitido
el atributo noise_estimate sera la probabilidad de deteccion
desde la cual se comienzara a trabajar


en caso de que el campo noise_estimate no este seteado
se tomara en cuenta el largo del comando emitido 
en base al historial/log de eventor (comandos) 
como probabilidad de deteccion 


2) aplicar la definicion termodinamica
de entropia es decir 

H(X) = -sumatoria(p(i)*log_2(P(i)))
donde p es la probabilidad 
i el evento 

entre una mayor entropia se
puntuara una mayor probabilidad de deteccion 

el objetivo idoneo es tener una baja entropia 

### evaluacion de tuneles para exfiltracion de informacion 

en el caso que se solicite una evaluacion 
sobre un mecanismo de exfiltracion  por parte de un LLM 

se debera de considerar los siguientes formatos de probabilidad
de deteccion dependiendo de los tipos de datos que se envien>

|tipo de dato| entropia en bits|
|------------|-----------------|
|texto plano|4.1|
|codigo fuente|5.2|
|imagenes jpeg| 7.6|
|datos cifrados|8.9|
|base64 encode|6.0|
|post compresion data|6.8|


ademas de ello se debe de considerar 
la capacidad de esteganografia para 
el camuflado de datos:

la entropia de los datos que se busacan exfiltrar es 

Entropia total del sistema original + N (informacion a exfiltrar)

tomar en cuenta implicaciones como el limite de shannon que establece que 

la longitud de una clave debe ser igual o mayor a la longitud del mensaje

adermas de ello se debe calculkar la entropia del formato de
datos que se quiere usar para exfiltrar la informaicon 
(por ejemplo wav o jpeg) y en base a ello comparar si 
la entropia del portador es mayor o igual a la entropia del mensaje oculto 

ejempo:

para ocultar  1mb de bytes de informacion 

se tiene una entropia de  4.1 bytes/bits 

esto quiere decir que el portador (archivo que se usara para exfiltrar informacion)
requiera de almenos 4.1 megabites de capacidad entropica 

en base a ello los formatos validos son 

1) imagenes comprimidas, archivos cifrados, audio 
y los formatos invalidos son texto plano html/xml o bases de datos estructurales 



este algoritmo se debe aplicar para situaciones como:

1) exfiltracion de datos por metodos como tuneles 
2) en una futura integracion con un MCP para analizar la probabilidad
de deteccion de algun metodo que al LLM se le ocurra integrar 

definicion del algoritmo
basada en termodinamica

el ruido se define como 

-log_2(P(evento))

donde P es la probabilidad y
evento es cada entrada captada en un historial o log de acciones
realizadas por el usuario

### pasos de aplicacion  del algorimo 

1) buscar con cheatIngestor el comando emitido
el atributo noise_estimate sera la probabilidad de deteccion
desde la cual se comienzara a trabajar


en caso de que el campo noise_estimate no este seteado
se tomara en cuenta el largo del comando emitido 
en base al historial/log de eventor (comandos) 
como probabilidad de deteccion 


2) aplicar la definicion termodinamica
de entropia es decir 

H(X) = -sumatoria(p(i)*log_2(P(i)))
donde p es la probabilidad 
i el evento 

entre una mayor entropia se
puntuara una mayor probabilidad de deteccion 

el objetivo idoneo es tener una baja entropia 

### evaluacion de tuneles para exfiltracion de informacion 

en el caso que se solicite una evaluacion 
sobre un mecanismo de exfiltracion  por parte de un LLM 

se debera de considerar los siguientes formatos de probabilidad
de deteccion dependiendo de los tipos de datos que se envien>

|tipo de dato| entropia en bits|
|------------|-----------------|
|texto plano|4.1|
|codigo fuente|5.2|
|imagenes jpeg| 7.6|
|datos cifrados|8.9|
|base64 encode|6.0|
|post compresion data|6.8|


ademas de ello se debe de considerar 
la capacidad de esteganografia para 
el camuflado de datos:

la entropia de los datos que se busacan exfiltrar es 

Entropia total del sistema original + N (informacion a exfiltrar)

tomar en cuenta implicaciones como el limite de shannon que establece que 

la longitud de una clave debe ser igual o mayor a la longitud del mensaje

adermas de ello se debe calculkar la entropia del formato de
datos que se quiere usar para exfiltrar la informaicon 
(por ejemplo wav o jpeg) y en base a ello comparar si 
la entropia del portador es mayor o igual a la entropia del mensaje oculto 

ejempo:

para ocultar  1mb de bytes de informacion 

se tiene una entropia de  4.1 bytes/bits 

esto quiere decir que el portador (archivo que se usara para exfiltrar informacion)
requiera de almenos 4.1 megabites de capacidad entropica 

en base a ello los formatos validos son 

1) imagenes comprimidas, archivos cifrados, audio 
y los formatos invalidos son texto plano html/xml o bases de datos estructurales 



este algoritmo se debe aplicar para situaciones como:

1) exfiltracion de datos por metodos como tuneles 
2) en una futura integracion con un MCP para analizar la probabilidad
de deteccion de algun metodo que al LLM se le ocurra integrar 

Resumen del algoritmo de scoring termodinámico / entropía
El objetivo es calcular la probabilidad de detección de actividades (comandos, eventos, exfiltraciones) utilizando el concepto de entropía de la información. El algoritmo mide ruido como:
- Ruido: -log₂(P(evento))
- Entropía: H(X) = -Σ p(i) * log₂(p(i)), donde p(i) es la probabilidad del evento i.
Mientras más alta es la entropía, mayor es la probabilidad de detección (más "ruido" en el sistema).
---
Implementación paso a paso
1. Buscar el comando emitido en cheatIngestor
- Al registrar un comando/evento, se busca en cheatIngestor si ya tiene un atributo noise_estimate (probabilidad de detección).
    - Si existe, se utiliza ese valor para el cálculo.
    - Si no existe, se estima la probabilidad en base a la frecuencia del comando (historial/log).
        - Comando más frecuente → menor probabilidad de detección
        - Comando raro/largo → mayor probabilidad
Pseudocódigo de obtención de probabilidad
def get_event_probability(evento, historial):
    # Si noise_estimate viene en el evento (por cheatIngestor), usalo
    if hasattr(evento, 'noise_estimate') and evento.noise_estimate is not None:
        return evento.noise_estimate
    # Si no, estimar por frecuencia en el historial
    total = len(historial)
    freq = sum(1 for e in historial if e.comando == evento.comando)
    prob = freq / total if total > 0 else 1.0
    return prob
---
2. Aplicar la definición termodinámica (entropía)
- Para el scoring global, calculá H(X) sobre la distribución de probabilidad de todos los eventos del historial:
    - Cada evento del historial cuenta como un tipo distinto (evento == comando ejecutado/acción registrada)
    - Si estás evaluando el sistema actual, usá el historial actual
import math
def calcular_entropia(historial):
    from collections import Counter
    total = len(historial)
    if total == 0:
        return 0.0
    counter = Counter(e.comando for e in historial)
    entropia = 0.0
    for count in counter.values():
        p_i = count / total
        entropia -= p_i * math.log2(p_i)
    return entropia
- Guardá la entropía junto con un mensaje de advertencia: más alta entropía = sistema más detectable.
---
3. Evaluación de túneles de exfiltración de información
Cuando el usuario o el sistema solicita una evaluación de un mecanismo de exfiltración o un comando de exfiltración, seguí estos pasos:
a. Determinar la Entropía del tipo de dato
Según la tabla:
Tipo de dato	Entropía (bits/byte)
texto plano	4.1
código fuente	5.2
imágenes jpeg	7.6
datos cifrados	8.9
base64 encode	6.0
post compresión	6.8
Ejemplo: Para exfiltrar 1 MB de datos cifrados:
- Entropía total ≈ 8.9 Mb
b. Capacidad de camuflaje y portador
- La entropía del portador debe ser ≥ entropía del mensaje a ocultar.
    - Ejemplos válidos: wav, jpeg, archivos comprimidos o cifrados, audio, video.
    - Inválidos: texto plano, HTML, XML, bases de datos con estructuras muy rígidas.
c. Algoritmo para validación de camuflaje (steganografía):
def puede_ocultar(portador_bits, entropia_portador, info_bits, entropia_info):
    # Capacidad total de portador para info oculta:
    capacidad = portador_bits * entropia_portador
    necesario = info_bits * entropia_info
    return capacidad >= necesario
Advertí al usuario si intenta camuflar datos con portadores de baja entropía!
---
4. Shannon Limit
Recordá que para cifrado perfecto (tipo one-time-pad), la longitud de la clave debe ser igual o mayor al mensaje.
- Incluí un chequeo extra para advertirle al usuario si su “clave” o método propuesto no cumple con esto al intentar “proteger” información de altísima entropía.
---
Situaciones de aplicación
1. Analizar commands/eventos históricos:  
   - Cada vez que se ingresa un comando al historial, actualizá/mostrá el “ruido” asociado usando la fórmula -log₂(P(evento))
   - Calculá la entropía global del sistema después de cada evento nuevo
2. Evaluar canales de exfiltración:
    - Al analizar protocolos/túneles propuestos, sumá la entropía esperada de los mensajes que planean pasar y compará contra la capacidad entropía del portador
    - Dejá evidencia si el canal es bajo “ruido” o de alta detección
3. MCP + LLM:  
   - En la futura integración:  
     - Cuando se evalúe una “idea”/suggest del LLM, calculá automáticamente su probabilidad de detección estimada en el scoring  
     - Si la acción involucra exfiltración, seguí los pasos de camuflaje y validación arriba
---
Resumen técnico para developers
- Implementar funciones auxiliares:
    - Cálculo de probabilidad por historial
    - Cálculo de entropía del sistema
    - Tabla de entropía por tipo de dato
    - Evaluador de camuflaje según portador/mensaje
- Integrar los hooks de scoring en:
    - Procesamiento de comandos en GatheringDB/Core
    - Módulo cheatIngestor para setear/consultar “noise_estimate”
    - UI: mostrar entropía/scoring actual y advertencias


### WORK

---
Historias de Usuario y Tasks para la Implementación del Algoritmo de Scoring Termodinámico
---

Historia 0:
Como operador quiero que EchoMaze tenga la funcionalidad para cargar logs o historiales de comandos  
para importar registros antiguos o externos y así poder analizarlos dentro del sistema.
---
Tasks técnicas:
1. Definir formatos soportados de logs/historiales
   - Identificar y detallar los formatos aceptados (e.g., texto plano tipo bash history, json, csv, custom propio, etc).


2. Agregar función para seleccionar/cargar archivos de logs
   - Crear función/método para seleccionar un archivo de log en la UI o CLI (--import-log path/to/file.log).
   - Validar existencia y permisos del archivo.
3. Implementar parser para logs/historiales
   - Parser para cada formato soportado.
       - Texto plano: extraer comandos uno por línea.
       - JSON: mapear propiedades relevantes.
       - CSV: mapear columnas (timestamp, comando, usuario, etc).
   - Manejar encoding y errores de formato.
4. Mapear eventos/parsing a modelo interno
   - Convertir cada entrada del log a la estructura interna de “evento”/“comando” de EchoMaze
   - Agregar metadatos: fuente, import_time, user, etc.
5. Guardar entradas importadas en la base de datos (DB/Core)
   - Insertar eventos uno a uno (o en bulk) persistiendo toda la información relevante.
   - Marcar origen como “importado” para trazabilidad.
6. Actualizar el historial actual con los nuevos eventos importados
   - Mezclar o extender el historial de comandos actualmente cargado.
   - Garantizar que los eventos importados queden disponibles para scoring/post-análisis.
7. Mostrar resumen de importación y advertencias
   - Indicar en CLI/UI la cantidad de eventos importados, errores detectados, entradas ignoradas, etc.
   - Mensajes claros si el formato no es reconocido.
8. Agregar tests de integración
   - Tests unitarios para parsers de cada formato.
   - Test de integración para confirmar que tras importar un log, los eventos aparecen correctamente en la base y UI.

---

---


Historia 1: Como operador quiero que cada comando o evento registrado tenga un "score de ruido" automático para entender la probabilidad de detección basada en mi historial
---
Tasks:
1. Agregar campo noise_score en el modelo de evento/comando  
   - Modificar modelo de eventos para incluir noise_score  
   - Asegurar persistencia en DB
2. Implementar función para buscar comando en cheatIngestor y obtener noise_estimate  
   - Consulta a cheatIngestor para cada comando registrado  
   - Si existe noise_estimate, usar ese valor
3. Desarrollar función fallback para estimar probabilidad de detección si no existe noise_estimate  
   - Calcular frecuencia del comando en historial
   - Definir función get_event_probability(evento, historial)
4. Calcular y guardar ruido como -log₂(P(evento)) al registrar cada acción  
   - Implementar cálculo y persistencia de noise_score
   - Hooks para ejecutar cálculo automáticamente al registrar evento
5. Mostrar ruido del comando en la UI  
   - Modificar TreeIPFrame (o interfaz CLI/UI) para reflejar el score de ruido asociado a cada comando
---
Historia 2: Como auditor o desarrollador quiero ver la entropía global de todos los eventos/historial para saber cuán detectable es el sistema
---
Tasks:
1. Implementar función para calcular entropía global (H(X)) del historial de eventos  
   - Distribución de probabilidad de todos los comandos/eventos
   - Función calcular_entropia(historial)
2. Generar advertencias automáticas según el valor de entropía  
   - Definir umbrales para advertencias (alta, media, baja entropía)
3. Mostrar la entropía y las advertencias en la UI/CLI  
   - Modificar interfaz para sumar sección de “entropía global del sistema”
   - Destacar visualmente si la entropía está por encima del umbral
---
Historia 3: Como pentester quiero que el sistema me ayude a evaluar la probabilidad de detección de técnicas de exfiltración según el tipo/cantidad de información y el método de transporte
---
Tasks:
1. Agregar utilidad/tarea de evaluación de exfiltración  
   - Crear comando o interfaz para evaluar una operación de exfiltración
2. Implementar tabla de entropía por tipo de dato  
   - Tabla con valores predefinidos (texto plano, código, imágenes, cifrado, etc.)
3. Calcular la entropía del mensaje a exfiltrar y la capacidad entropía del portador  
   - Función para calcular entropía total del mensaje
   - Función para calcular capacidad efectiva del portador
4. Advertir si la exfiltración es viable/camuflable según el canal  
   - Comparar entropía del canal vs. entropía del mensaje
   - Generar mensaje de alerta en caso de riesgo alto
5. Mostrar resultado y recomendaciones en CLI/UI  
   - Agregar salida clara indicando si la exfiltración es plausible y qué formatos convienen
---
Historia 4: Como arquitecto quiero que el sistema esté preparado para permitir la futura integración con un MCP o LLM que evalúe automáticamente métodos y canales usando la fórmula de entropía
---
Tasks:
1. Abstraer lógica de scoring y entropía en módulos reutilizables (helpers/utils)  
   - Refactor para separar lógica del scoring y evaluación de exfiltración
2. Definir interfaz/fachada para módulos externos (MCP, LLM, etc.)  
   - Documentar y exponer funciones clave (cálculo de ruido, entropía, evaluación de canal/portador)
   - Preparar stubs/mockups para integración API
3. Agregar hooks en módulos Core y GatheringDB para que otros sistemas puedan pedir scoring/entropía  
   - Añadir métodos públicos y tests unitarios
4. Generar documentación para desarrolladores sobre uso e integración  
   - Instrucciones claras para equipos que quieran conectar LLM o MCP al engine de scoring
---
¿Cómo avanzar?
- Recomiendo empezar por la Historia 1: así cada evento ya guarda su “ruido”, y después sumás la capa global (Historia 2), layer de exfiltración (Historia 3) y luego la interfaz de integración (Historia 4).
- Si querés el desglose aún más atómico en sub-tasks de código Python, avisame y lo bajo a funciones/módulos/clases.
