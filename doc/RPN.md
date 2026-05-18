 1. Noise Scoring per Action/IP: DESARROLLADO
Métrica de exposición: El modelo Actions y la entidad IPNode en GATHERINGDB/model.py guardan el score.
Cálculo en tiempo real: Hemos implementado core/entropy.py que calcula el noise_score de cada comando mediante entropía termodinámica. Las funciones en ScoringEngine (core/scoring.py) y los hooks en los CRUD de la DB (GATHERINGDB.main y crud_mitre) incrementan el score automáticamente.
Agregación por Pivot Path: La función ScoringEngine.aggregate_pivot_noise() suma los scores de las rutas de pivote y ya está integrada con la UI (TreeIPFrame y el OpSecPanel).
🟢 2. Tactical Suggestions Engine: DESARROLLADO
Sugerencia de estrategias y comandos: La clase TacticalSuggestions (en core/tactical_suggestions.py) implementa la lógica para detectar el contexto y dar consejos.
El TerminalFrame y SuggestionsFrame hacen uso de model.get_suggestions_for_ip(ip), conectándose con cheatIngestor para recomendar vectores de ataque según los puertos/servicios de la máquina actualmente seleccionada.
🟢 3. Profile-Lowering Advice: DESARROLLADO
Tips Automáticos de Stealth: La función TacticalSuggestions.get_noise_advice(score) entrega alertas específicas según el nivel de ruido (e.g., "Stealth optimal", "High noise!", "Critical exposure").
Además, gracias a la Historia 2 (Entropía global), la UI detecta si el sistema general se vuelve muy predecible (alta entropía/detectabilidad) y muestra estas advertencias en el OpSecPanel de la interfaz.
🟡 4. LLM/MCP Integration Hooks: MAYORMENTE DESARROLLADO
Stubs, interfaces y Event Hooks: Desarrollado. El sistema usa un patrón Observer / Observable (UI/models.py) donde los eventos (score_changed, tactics_changed) disparan actualizaciones no bloqueantes. Además, expusimos APIs como evaluate_exfiltration explícitamente diseñadas para integrarse con MCP.
Faltante: La especificación pide "hooks for future LLM/MCP". Los ganchos (hooks) a nivel de código existen e intermedian a través de OpSecHooks, pero lógicamente aún no hay un servidor MCP o cliente LLM real programado (lo cual es correcto, ya que el documento dice "future LLM/MCP-driven adaptive advice").
🟢/🟡 5. Requerimientos No Funcionales & Arquitectura
No bloquear UI/CLI (Asincronía): Desarrollado. En UI/opsec_panel.py utilizamos threading.Timer con lógica de debounce (120ms) para que, al procesar sugerencias o emitir ruido en masa, no se trabe el shell interactivo.
Retrocompatibilidad: Desarrollado. No se rompieron esquemas viejos, e integramos las nuevas validaciones transparentemente vía LogImportManager y el motor de Scoring.
Testeabilidad: Desarrollado. Existen múltiples unit tests (test_scoring.py, test_opsecCRUD.py, test_observer_integration.py, tests de entropía).
Feature Toggles (Interruptores para apagar sugerencias): FALTANTE / PARCIAL. El documento indica: "Feature toggles SHOULD allow enabling/disabling advice/suggestions/scoring modules individually." Actualmente, los paneles de UI (OpSecPanel) se inicializan por defecto. No hemos añadido una bandera (--disable-opsec) o un archivo config.json para encender o apagar por completo este subsistema en tiempo de ejecución.



### AREAS DE OPORTUNIDAD

✦ Basado en la arquitectura actual de EchoMaze y las implementaciones que hemos realizado (serialización, multi-agentes, carga dinámica de herramientas), he identificado las siguientes áreas de oportunidad
  estratégicas para llevar el proyecto al siguiente nivel:

  1. Orquestación y Colaboración Multi-Agente (Swarm)
  Actualmente tienes agentes especializados (OSINT, Maldev, etc.), pero operan de forma aislada.
   * Oportunidad: Implementar un Agente Orquestador que reciba una orden compleja (ej. "compromete la IP 10.10.10.5") y delegue subtareas automáticamente a los agentes especializados.
   * Beneficio: Transforma a EchoMaze de un "asistente de chat" a una plataforma de ejecución autónoma guiada.

  2. Integración de Evidencias y Generación de Reportes
  El sistema ya gestiona nodos IP, puertos y artefactos.
   * Oportunidad: Crear un módulo de Reporting Dinámico que exporte todo el historial de la base de datos GATHERINGDB a formatos como Markdown o PDF, organizados por la Cyber Kill Chain.
   * Beneficio: Automatiza la parte más tediosa de un Pentest: la documentación final.

  3. Simulación de Adversarios (Playbooks)
  Tienes un sistema de "Skills" y "Tools" cargables por JSON.
   * Oportunidad: Desarrollar Playbooks de Intrusión (archivos YAML/JSON) que definan secuencias de comandos para técnicas específicas (ej. movimiento lateral vía WinRM). Los agentes podrían "leer" estos
     playbooks para ejecutar ataques complejos paso a paso.
   * Beneficio: Estandariza las operaciones y permite reutilizar tácticas exitosas en diferentes objetivos.

  4. Visualización de la Ruta de Pivote (Grafo)
  La UI actual es basada en texto (asciimatics) y usa una estructura de árbol.
   * Oportunidad: Implementar una Vista de Grafo de Red (similar a BloodHound) dentro de la CLI o mediante una exportación HTML/D3.js que muestre visualmente los saltos (pivoting) necesarios para llegar a un
     objetivo crítico.
   * Beneficio: Facilita la comprensión de redes complejas con múltiples capas de aislamiento.

  5. Análisis Predictivo de OpSec (Machine Learning)
  Ya cuentas con un ScoringEngine y análisis de entropía.
   * Oportunidad: Entrenar un modelo pequeño de ML (o usar el LLM con RAG) para predecir la Probabilidad de Detección basada en el historial de comandos ejecutados y la configuración de seguridad del objetivo.
   * Beneficio: Proporciona advertencias proactivas ("Este comando tiene un 80% de probabilidad de alertar al EDR en este contexto").

  6. Soporte para Protocolos de Comando y Control (C2)
  EchoMaze gestiona túneles e implantes.
   * Oportunidad: Integrar EchoMaze como un Frontend para C2 existentes (como Sliver o Havoc) mediante APIs.
   * Beneficio: Permitiría que los agentes de EchoMaze interactúen directamente con sesiones de shell activas para ejecutar herramientas de post-explotación.