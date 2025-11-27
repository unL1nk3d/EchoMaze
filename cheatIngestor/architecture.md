# CHEAT INGESTOR

este es un ingestor dedicado para poder alimentar al sistema con cheatsheets desarollados por el operador
para ayudar al operador en tiempo real a autocompletar / sugerir comandos durante una shell 

el ingestor como tal utilizara un fromato similar a 

```json
"techniques":[
{
"technique":"T1021.002",
  "name": "Remote Services - SSH",
    "template":
        {"desc": "Local port forward via SSH (operator to target via pivot)",
        "linux": "ssh -L {local_port}:{target_ip}:{target_port} {user}@{jump_host} -p {jump_port}",
        "windows": "plink.exe -L {local_port}:{target_ip}:{target_port} {user}@{jump_host} -P {jump_port}",
        "noise_estimate": 0.3,
        }
  }
]
```


el ingestor recibira estos datos y los almacenara en el CRUD definido en GATHERINGDB CRUD_Template


se puede usar un modelo como Ollama para autoamticamente generar cheatsheets en formato md para poder ayudar al sistema a que ingiera estos datos


como tal existe una tabla en sql que se puede confundir con el propostio de cheatingestor es actions
el motivo del por que tener un actions repository CRUD en sqlite es por que este actions se usara para asociar un conjunto de accioens que se realizo con una direccion ip (es decir que efectivamente lanzo el operador)
un
`-- Historico de acciones / comandos sugeridos / ejecutados`

ademas actions asociara estos comandos emitidos con un mitre_ttp_id que encuentre

en cambio el proposito de chet ingestor es simplemente sugerir comandos basados en el mitre

FTS5 es la opción más ligera y robusta.
No necesitas vector DB ni Elastic a menos que quieras búsquedas semánticas (ej. “quiero un túnel” → sugerir ssh -L).


