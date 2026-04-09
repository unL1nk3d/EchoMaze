# EchoMaze Operator Guidance + Tunel Management + Dynamic OPSEC — Tasks

## I. DB/DAO & Persistencia
- [ ] Actualizar modelos DAO: scoring (por IP/acción), perfil/agresividad, gestión de túneles
    - **Requisito para: Core lógica, UI y CLI**
- [ ] Migraciones (si aplica)

## II. Core Lógica & Servicios
- [ ] Motor de scoring de ruido (ajustable dinámicamente)
    - **Depende de: Modelos DAO**
- [ ] Motor de recomendaciones OPSEC (extensible/hooks LLM/MCP)
    - **Depende de: Scoring y perfil/agresividad**
- [ ] CRUD gestión de túneles (+ edgecase rootless)
    - **Depende de: Modelos DAO**

## III. Interfaces de Usuario
### CLI
- [ ] Comandos: crear, listar, eliminar túneles
    - **Depende de: Core gestión de túneles**
- [ ] Comando para ajuste de perfil/agresividad en runtime
    - **Depende de: Motor perfiles/agresividad**
- [ ] Visualización CLI: score de ruido y sugerencias OPSEC
    - **Depende de: Motor scoring y recomendaciones**

### TUI (asciimatics)
- [ ] Visualización scoring y recomendaciones en UI
    - **Depende de: Motor scoring y recomendaciones**
- [ ] Panel/configuración de perfil/agresividad “en caliente”
    - **Depende de: Motor perfiles/agresividad**

## IV. Edgecase/Advertencias
- [ ] Feedback CLI/TUI: impedir túnel rootless sin IP alcanzable
    - **Depende de: Core CRUD de túneles, comandos UI/CLI**

## V. Testing
- [ ] Unit tests: scoring, perfiles, CRUD túneles, edgecases
- [ ] Integración: CLI/TUI/DB, ajuste de perfil/agresividad
- [ ] UI tests: visualización y feedback en asciimatics
    - **Dependen de: features implementadas**

---

> Este archivo almacena el scope y tasks detallados de la iniciativa actual para referencia permanente.
