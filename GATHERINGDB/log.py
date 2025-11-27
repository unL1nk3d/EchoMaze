import logging as log 

#log.basicConfig(level=log.DEBUG)# seteamos el nivel de debug por desarollo
log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        log.FileHandler("db_logs.log")
    ]
)
    
log.debug("INICIO RECOPILADO".center(50,"="))# mandamos mensaje a nivel debug
# dependiendo del nivel solo se muestran niveles superiores o el nivel debug

# configuracion por ddefecto es warning

# handler un handler
"""
es un recurso a donde enviar la informacion de debugeo

ademas de usar un handler es posible especificar el formato del logueo 
log.basicConfig(level=log.DEBUG,format='%(asctime)s: %(levelname)s [%(filenames])]' )
# asctime es el tiempo

la ultima linea agrega el archivo del error



"""