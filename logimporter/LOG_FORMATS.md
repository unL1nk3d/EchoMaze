# EchoMaze Log Import Formats

## Formatos Soportados

Este documento describe los formatos de logs/historiales que EchoMaze puede importar.

### 1. **Texto Plano (TXT)**
- Un comando por línea
- Opcional: timestamp al inicio (separado por `|`, `:` o tab)
- Encoding: UTF-8, ISO-8859-1

**Ejemplo:**
```
2024-01-15 10:30:45 | whoami
2024-01-15 10:31:00 | ls -la /etc
id
hostname
```

**Parser reconoce:**
- `YYYY-MM-DD HH:MM:SS | comando` (con timestamp)
- `comando` (sin timestamp, usa import_time)

---

### 2. **JSON**
- Array de objetos con estructura flexible
- Campos esperados: `command`, `timestamp`, `operator`, `user`, `shell`
- Campos opcionales: `hostname`, `exit_code`, `description`

**Ejemplo:**
```json
[
  {
    "command": "whoami",
    "timestamp": "2024-01-15T10:30:45Z",
    "operator": "admin",
    "user": "root",
    "shell": "/bin/bash"
  },
  {
    "command": "ls -la /etc",
    "timestamp": "2024-01-15T10:31:00Z",
    "operator": "admin",
    "user": "root"
  }
]
```

---

### 3. **CSV**
- Delimitador: `,` (coma) o `;` (punto y coma)
- Primera fila: headers (case-insensitive)
- Campos esperados: `command`, `timestamp`, `operator`, `user`
- Campos opcionales: `hostname`, `exit_code`, `description`

**Ejemplo:**
```csv
command,timestamp,operator,user,hostname
whoami,2024-01-15 10:30:45,admin,root,target-01
ls -la /etc,2024-01-15 10:31:00,admin,root,target-01
id,2024-01-15 10:31:15,admin,root,target-01
```

---

### 4. **Bash History**
- Formato nativo de `~/.bash_history`
- Líneas con tiempo (si bash fue compilado con `HISTTIMEFORMAT`)
- Formato: `#<timestamp>` seguido de comando

**Ejemplo:**
```
#1705316445
whoami
#1705316460
ls -la /etc
id
```

---

### 5. **Zsh History**
- Formato EXTENDED_HISTORY de Zsh
- Estructura: `: <timestamp>:<elapsed>;<comando>`

**Ejemplo:**
```
: 1705316445:0;whoami
: 1705316460:0;ls -la /etc
: 1705316475:0;id
```

---

### 6. **Windows PowerShell History**
- Formato XML o texto plano (por defecto en Windows)
- Ubicación típica: `C:\Users\<user>\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt`

**Ejemplo:**
```
Get-Process
Get-ChildItem C:\
whoami
```

---

### 7. **Custom JSON Lines (JSONL)**
- Una línea JSON por comando
- Estructura similar a JSON, pero línea por línea

**Ejemplo:**
```jsonl
{"command":"whoami","timestamp":"2024-01-15T10:30:45Z","operator":"admin"}
{"command":"ls -la /etc","timestamp":"2024-01-15T10:31:00Z","operator":"admin"}
```

---

## Campos Normalizados

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `command` | string | ✅ | Comando ejecutado |
| `timestamp` | string (ISO 8601 o YYYY-MM-DD HH:MM:SS) | ❌ | Momento de ejecución |
| `operator` | string | ❌ | Usuario/operador que ejecutó |
| `user` | string | ❌ | Usuario en el sistema |
| `shell` | string | ❌ | Shell usado (bash, zsh, powershell, etc) |
| `hostname` | string | ❌ | Host donde se ejecutó |
| `exit_code` | int | ❌ | Código de salida del comando |
| `description` | string | ❌ | Notas/descripción adicional |

---

## Detección Automática de Formato

EchoMaze intenta detectar el formato automáticamente:
1. Primero intenta JSON
2. Luego JSONL
3. Luego CSV (detecta delimitador)
4. Luego Bash History / Zsh History
5. Finalmente Texto Plano

Si falla, solicita al usuario que especifique el formato.

---

## Validación y Manejo de Errores

- **Líneas vacías**: Ignoradas
- **Líneas con formato inválido**: Registradas en reporte (no causan fallo)
- **Timestamps inválidos**: Usa `import_time` del sistema
- **Comandos vacíos**: Ignorados
- **Encoding inválido**: Intenta conversión UTF-8 fallback
