| ip | parent_ip       |
|----|-----------------|
| 192.168.1 | 172.16.1 |

el usuario presiona CTRL + O

| ip | parent_ip         |
|----|-------------------|
| * 192.168.1 | 172.16.1 |

el usuario selecciona una ip usando las flechas de arriba o abajo
la tabla automaticamente se reducira solo mostrando 2 opciones a menos que se use 
CTRL + OI que mostrara 10 opciones cada vez que el usuario desplaze hasta abajo de las 10 opciones cargadas

| ip | parent_ip         |
|----|-------------------|
| * 192.168.1 | 172.16.1 |
    +-----------+
    |  SMB      |
    |  FTP      |
    |  SSH      |
    +-----------+

el usuario podra desplegar un cuadro de opciones con los protocolos que esta direccion ip tiene asociados



```shell

bg nmap -sS -n -oG inform.txt 192.168.30.2 

[ctrl + S] <--- se despliega el mock

| ip | parent_ip       |
|----|-----------------|
| 192.168.1 | 172.16.1 |

[ctrl + c] <---- se cierra el mock

echo "hello"
```




```

 MENSAJE 1 <--- layout de 1 solo espacio
| ip | parent ip | <-- layout de 2 espacios que almacena 2 listbox
|----|-----------|


```