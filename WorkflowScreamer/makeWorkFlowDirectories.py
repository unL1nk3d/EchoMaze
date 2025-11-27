import os

# Lista de nombres de directorios
work_dirs = ['context', 'exploits', 'scan']

def make_dirs(base_path):
    # Crear cada directorio si no existe
    for dir_name in work_dirs:
        os.makedirs(os.path.join(base_path,dir_name), exist_ok=True)
