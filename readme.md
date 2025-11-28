# descripcion:
EchoMazees una base de datos ligera y modular para gestionar direcciones IP en entornos de pentesting, ayudando a organizar escenarios de pivoting y mantener un registro claro de los objetivos, posee capacidades para sugerir comandos al operador en escenarios específicos para ayudar a mapear el nivel de ruido que genera en una prueba de penetración mediante un sistema de puntos además de consejos a seguir para mantener un perfil bajo durante las intrusiones de forma similar a herramientas como bloodhound


# Avances actuales del proyecto

El desarrollo ha progresado de manera significativa en torno a la gestión y visualización de direcciones IP escaneadas.

Gestión de IPs en base de datos local Se implementó un sistema que permite almacenar las direcciones IP escaneadas en una base de datos local, lo que facilita su consulta y actualización.

Se añadieron funciones de búsqueda, actualización e inserción.

Se incorporaron validaciones para evitar duplicados y se diseñaron errores personalizados para mejorar la robustez del sistema.

Se resolvió el bug relacionado con la caché, que anteriormente no almacenaba direcciones IP que no provenían directamente de Nmap.

Control dinámico de profundidad en el árbol de IPs Se avanzó en la funcionalidad que permite modificar dinámicamente el nivel de profundidad mostrado en el árbol de direcciones IP.

Ahora es posible ajustar la visualización para navegar entre direcciones hijas y padres.

Se añadió la opción de incrementar la profundidad mediante la interacción con el símbolo +, lo que brinda mayor flexibilidad al usuario.

Visualización en la interfaz TUI Se integró la capacidad de mostrar en la interfaz de usuario en modo texto (TUI) las direcciones IP hijas asociadas a una dirección IP padre. Esto mejora la comprensión jerárquica de la información y facilita la exploración de relaciones entre nodos.

Estructuración automática de resultados Cada dirección IP escaneada se convierte automáticamente en un directorio estructurado que contiene sus puertos y servicios detectados. Esta organización sistemática permite un acceso más claro y ordenado a la información obtenida durante los escaneos.

