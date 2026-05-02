

1. Integración real con MCP server y LLM/AI  
   - Solo se menciona como meta (“planea integrar un servidor MCP y capacidades LLM para consulta/almacenamiento inteligente”).  
   - Faltante: Implementar agente MCP para consulta/salvado vía LLM (actualmente parece concepto, no código).
2. Automatización avanzada de sugerencias contextuales
   - El objetivo es sugerir comandos útiles en cada contexto/escenario de pentest.
   - No se detalla el sistema de reglas/contexto para esto.
   - Faltante: Motor de sugerencias inteligentes, probablemente basado en historial, heurísticas o integración con cheat sheets (quizás vinculado a cheatIngestor, pero no especificado del todo).
3. Sistema de scoring de “ruido”/detección de perfil bajo
   - Se comenta que se quiere mapear el “nivel de ruido” (ej: actividades ruidosas como nmap) usando puntuaciones.
   - No se describe un subsistema o modelo para esto.
   - Faltante: Algoritmo de scoring con indicadores, integración con workflow y presentación al usuario.
4. Tips y recomendaciones proactivas de OPSEC
   - El objetivo es asistir tipo BloodHound, con sugerencias de bajo perfil.
   - No está claro si existe un motor de recomendaciones hoy en el código.
   - Faltante: Módulo que analice acciones pasadas y sugiera, advierta o recomiende prácticas de OPSEC.
5. Cobertura de tests y TDD
   - El workflow sugiere usar TDD, pero no hay info explícita sobre cobertura, tests críticos o faltantes.
   - Potencial faltante: Tests adicionales para corner cases, branches complejos o integración.
6. UI features avanzadas
   - La UI actual es CLI en asciimatics y muestra árbol de IPs con datos básicos.
   - Faltante: 
     - Visualizaciones más ricas (gráficas, hojas de ruta pivoting).
     - Edición avanzada y drag&drop en CLI.
     - Alerts contextuales, filtros o exportación avanzada.
7. Importación/extensión para otros tipos de scan
   - El importer presente es para nmap (gnmap).
   - Faltante: Soporte para archivos Nessus, OpenVAS, o SSV, o integración con otras fuentes de descubrimiento.


# TODO
EPICA: Quiero que se tenga una base de datos diferente que se use para gestionar la seguridad operacional del entorno
de tal forma que en ella se contemplen multiples tecnicas de forwarding/intrusion y se cotejen respecto al MITRE para poder
proveer al operador de tanto una shell interactiva que sugiera comandos y que cada comando contrnga un puntaje de nivel de sigilo asociado asi como riesgo de dar con el operador

EPICA: Quiero que la herramienta exporte datos compatibles 
con Dradis, Faraday o Visual Map para facilitar la 
interoperabilidad. 


Quiero que la herramienta genere reportes en formato 
Markdown basados en los hallazgos por IP. 

Quiero acceder rápidamente a los directorios de una IP 
específica mediante combinaciones de teclas, sin usar 
comandos manuales. 


Quiero que los servicios detectados se etiqueten y se 
visualicen en la estructura de carpetas para identificar 
vectores de ataque. 

Quiero que los datos de escaneo y reportes estén 
protegidos contra escritura no autorizada para 
mantener su integridad. 

Quiero que Turbo-Disco funcione en sistemas Linux sin 
dependencias pesadas para usarla en entornos de 
pentesting reales. 



# PROCESS



* Quiero tener una terminal que directamente me proponga comandos para poder realizar pivoring 

* para emitir sugerencias quiero que estas se carguen desde un cheatsheet con un formato especifico
    * modificar el launch.py para agregar un 
* quiero que los cheatsheets se guarden en una base de datos relacional sql para facilitar las consutlas posterior a ser ingeridos por el cheatingestor





# DONE

* Quiero que dependiendo de una direccion ip seleccionada se puedan emitir sugerencias sobre como realizar pivoting para llegar hasta esa direccion ip
    * para emitir sugerencias quiero que estas se carguen desde un cheatsheet con un formato especifico
    * quiero que los cheatsheets se guarden en una base de datos relacional sql para facilitar las consutlas posterior a ser ingeridos por el cheatingestor
* Quiero poder pegar los comandos de sugerencia en mi terminal de preferencia
* Quiero tener una terminal que directamente me proponga comandos para poder realizar pivoring 



---

# DONE

* Quiero que las IPs escaneadas se almacenen en una base de 
datos local para consultarlas y actualizarlas fácilmente.
    * buscar
    * actualizar
    * insertar
        * custom errors
        * omitir ips que ya existan
    * resolver bug de que cache no almacena direciones ip que no se hayan cargado desde nmap

* quiero que se pueda editar el nivel de profunidad a mostrar para cambiar dinamicamente entre direcciones ip hijas

* Quiero que se pueda modificar dinamicamente al pulsar + el nivel de profundidad a ir en el arbol de direcciones ip 

* Quiero que se muestre en el TUI las direcciones IP hijas de una direccion ip padre 
---

* Quiero que cada dirección IP escaneada se convierta 
automáticamente en un directorio estructurado con sus 
puertos y servicios.

* Quiero que las IPs escaneadas se almacenen en una base de 
datos local para consultarlas y actualizarlas fácilmente.
    * buscar
    * actualizar
    * insertar
        * custom errors
        * omitir ips que ya existan
    * resolver bug de que cache no almacena direciones ip que no se hayan cargado desde nmap

* quiero que se pueda editar el nivel de profunidad a mostrar para cambiar dinamicamente entre direcciones ip hijas

* Quiero que se pueda modificar dinamicamente al pulsar + el nivel de profundidad a ir en el arbol de direcciones ip 

* Quiero que se muestre en el TUI las direcciones IP hijas de una direccion ip padre 
---

* Quiero que cada dirección IP escaneada se convierta 
automáticamente en un directorio estructurado con sus 
puertos y servicios.

---

* Quiero que dependiendo de una direccion ip seleccionada se puedan emitir sugerencias sobre como realizar pivoting para llegar hasta esa direccion ip

* Quiero poder pegar los comandos de sugerencia en mi terminal de preferencia

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
   