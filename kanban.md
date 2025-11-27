

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
---

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

---