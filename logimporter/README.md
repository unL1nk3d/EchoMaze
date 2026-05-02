# EchoMaze Log Import - Documentación de Uso

## Resumen

La funcionalidad de importación de logs permite cargar historiales de comandos desde múltiples formatos y guardarlos en la base de datos de EchoMaze para análisis y scoring posterior.

## Formatos Soportados

EchoMaze soporta los siguientes formatos de logs:

1. **PlainText** - Texto plano, un comando por línea
2. **JSON** - Array de objetos con metadatos
3. **JSONL** - JSON Lines (una línea JSON por comando)
4. **CSV** - Valores separados por comas o punto y coma
5. **BashHistory** - Formato nativo de `~/.bash_history`
6. **ZshHistory** - Formato EXTENDED_HISTORY de Zsh
7. **PowerShellHistory** - Historial de PowerShell

Para más detalles sobre cada formato, ver `logimporter/LOG_FORMATS.md`

## Uso desde CLI

### Importar desde archivo con auto-detección de formato

```bash
python launch.py --import-log /ruta/al/archivo.log
```

### Importar especificando el formato

```bash
python launch.py --import-log /ruta/al/archivo.log --log-format JSON
```

### Importar con operator (usuario) asociado

```bash
python launch.py --import-log /ruta/al/archivo.log --log-operator "admin"
```

### Opciones disponibles

- `--import-log <path>` - Ruta al archivo de log (obligatorio)
- `--log-format <format>` - Formato del log (opcional, auto-detecta si no se especifica)
  - Valores: `PlainText`, `JSON`, `JSONL`, `CSV`, `BashHistory`, `ZshHistory`, `PowerShellHistory`
- `--log-operator <name>` - Nombre del operador a asociar con los comandos (opcional)

## Uso Programático

### Importar desde archivo

```python
from logimporter import LogImportManager
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.main import CRUD_GATHERINGDB

# Inicializar CRUD
dao = GenericDAO()
crud = CRUD_GATHERINGDB(dao)

# Crear gestor
mgr = LogImportManager(crud=crud)

# Importar
imported_count, report = mgr.import_from_file(
    filepath="/ruta/al/log.txt",
    format_hint="PlainText",  # Opcional
    operator="admin"
)

print(report)  # Mostrar reporte
print(f"Importados: {imported_count} comandos")
```

### Importar desde contenido de string

```python
from logimporter import LogImportManager

mgr = LogImportManager(crud=crud)

content = """
whoami
ls -la /etc
id
"""

imported_count, report = mgr.import_from_content(
    content=content,
    operator="admin"
)
print(report)
```

### Validar parámetros antes de importar

```python
from logimporter import validate_import_params

valid, error = validate_import_params(
    filepath="/ruta/al/archivo",
    format_hint="JSON"
)

if not valid:
    print(f"Error: {error}")
else:
    # Proceder con importación
    pass
```

## Reporte de Importación

Cada importación retorna un objeto `ImportReport` con las siguientes métricas:

```
============================================================
IMPORT REPORT
============================================================
Format Detected: JSON
Total Lines Processed: 100
Imported Commands: 95
Skipped Lines: 5
Success Rate: 95.0%

⚠️  WARNINGS (2):
  - Line 5: Timestamp could not be parsed, using system time
  - Line 8: Unknown field 'extra_field' (ignored)

❌ ERRORS (3):
  - Line 10: Missing 'command' field
  - Line 15: Command cannot be empty
  - Line 20: Invalid JSON

============================================================
```

## Ejemplos de Logs

### Plain Text

```
whoami
ls -la /home
id
hostname
```

Con timestamps:

```
2024-01-15 10:30:45 | whoami
2024-01-15 10:31:00 | ls -la /home
```

### JSON

```json
[
  {
    "command": "whoami",
    "timestamp": "2024-01-15T10:30:45Z",
    "operator": "admin",
    "user": "root"
  },
  {
    "command": "ls -la /home",
    "timestamp": "2024-01-15T10:31:00Z",
    "operator": "admin"
  }
]
```

### CSV

```csv
command,timestamp,operator,user
whoami,2024-01-15 10:30:45,admin,root
ls -la /home,2024-01-15 10:31:00,admin,root
id,2024-01-15 10:31:15,admin,root
```

### Bash History

```
#1705316445
whoami
#1705316460
ls -la /home
id
```

### Zsh History

```
: 1705316445:0;whoami
: 1705316460:0;ls -la /home
: 1705316475:0;id
```

## Modelo de Datos

Los eventos importados se mapean a la entidad `Actions` en GATHERINGDB:

```python
@dataclass
class Actions:
    id: int                    # Auto-generado
    node_id: int              # ID del nodo IP (opcional)
    action_type: str          # "imported_command"
    command_template: str     # El comando
    parameters: str           # Parámetros (vacío para logs importados)
    mitre_ttp_id: str         # ID MITRE (opcional)
    timestamp: str            # ISO 8601 (o import_time si no se especifica)
    operator: str             # Usuario que ejecutó
    noise_score: float        # Score de ruido (se calcula después)
```

## Integración con Scoring

Los comandos importados pueden ser analizados posteriormente por el ScoringEngine para calcular su `noise_score` (probabilidad de detección) basado en:

1. Frecuencia del comando en el historial
2. Técnicas MITRE asociadas
3. Entropía del historial global

Esto se realizará en la Historia 1 del algoritmo de scoring termodinámico.

## Manejo de Errores

### Archivo no encontrado

```
[!] Import validation failed: File not found: /ruta/inexistente
```

### Formato no soportado

```
[!] Unknown or unsupported format: UNKNOWN_FORMAT
```

### Contenido inválido

El reporte indicará líneas específicas que no pudieron procesarse, permitiendo al operador revisar y corregir.

## Testing

Ejecutar la suite de tests:

```bash
python -m unittest test.test_logimporter -v
```

Tests disponibles:
- `TestCommandEvent` - Validación de eventos
- `TestImportReport` - Generación de reportes
- `TestPlainTextParser` - Parser de texto plano
- `TestJSONParser` - Parser JSON
- `TestCSVParser` - Parser CSV
- `TestBashHistoryParser` - Parser Bash History
- `TestZshHistoryParser` - Parser Zsh History
- `TestLogFormatDetector` - Auto-detección de formatos
- `TestLogImporter` - Integración general
- `TestLogImportValidator` - Validación de parámetros
- `TestLogImportManagerIntegration` - Integración con GATHERINGDB

## Próximos Pasos

1. **Historia 1**: Implementar scoring automático para cada comando importado
2. **Historia 2**: Mostrar entropía global del historial en la UI
3. **Historia 3**: Evaluar túneles y métodos de exfiltración
4. **Historia 4**: Integración con MCP/LLM para análisis automático

## Preguntas Frecuentes

**¿Qué pasa si un comando está vacío?**
Se ignora y se registra en el reporte como error.

**¿Puedo importar múltiples archivos?**
Sí, ejecuta `--import-log` múltiples veces (actualmente ejecuta uno por llamada).

**¿Se pierden los datos anteriores al importar?**
No, los nuevos comandos se añaden a la base de datos existente.

**¿Cómo puedo ver todos los comandos importados?**
```python
actions = generic.get_all_actions()
for action in actions:
    print(f"{action.timestamp} | {action.operator} | {action.command_template}")
```

**¿Qué pasa si hay timestamps duplicados?**
Se guardan normalmente; la base de datos permite duplicados en `timestamp`.
