import os
from typing import Generator
from GATHERINGDB.dao import GenericDAO,Transaction
from GATHERINGDB.model import IPNode,Ports
from GATHERINGDB.init_db import DatabaseInitializer
from GATHERINGDB.log import log



class CRUD_GATHERINGDB:
    def __init__(self, dao:GenericDAO=None):
        self.dao = dao
    def check_field_n_value(self,field:str,value:str):
        if not(isinstance(field,str) and isinstance(value,str)):
            raise ValueError("Field and value must be strings")
    def select_ip_by_field(self,field:str,value:str,dao:GenericDAO=None) -> list[IPNode]:
        self.check_field_n_value(field,value)
            
        try:
            nodes = dao.seleccionarCoincidencia(IPNode,field,value)
            return nodes
        except Exception as e:
            log.error(f"[-] error selecting nodes by field \n {e}")
            return []  
    def select_port_by_field(self,field:str,value:str,dao:GenericDAO=None) -> list[Ports]:
        self.check_field_n_value(field,value)
        try:
            node = dao.seleccionarCoincidencia(Ports,field,value)
            return node
        except Exception as e:
            log.error(f"[-] error selecting nodes by field \n {e}")
            return []
    def insert_port_node(self,ip_id,ports,service_name='unknown',dao:GenericDAO=None):
        try:
            data =dao.seleccionarPorId(IPNode,ip_id)
            if not data:
                raise ValueError(f"No IPNode found with id {ip_id}")
            ports = Ports(id=0,port=ports,service_name=service_name,ip=data.ip)
            dao.insertar(ports)
        except Exception as e:
            log.error(f"[-] error inserting node \n {e}")
    def insert_ip(self,ip:str,current_path:str,parent_ip:str,child_level:int=0,dao:GenericDAO=None):
        node = IPNode(id=0,ip=ip, parent_ip=parent_ip,child_level=child_level,path=current_path)
        dao.insertar(node)
    def show_all_data(self,data,dao:GenericDAO=None):
        nodes = dao.seleccionar(data)
        for node in nodes:
            print(node)
        return len(nodes)
    def select_all_ips(self,dao:GenericDAO=None) -> list[IPNode]:
        return dao.seleccionar(IPNode)
    def select_depth_ips(self,depth:int,dao:GenericDAO=None) -> list[IPNode]:
        return dao.seleccionarCoincidencia(IPNode,'child_level',depth)
    def select_ip_parents(self,parent_ip:str,depth:int,dao:GenericDAO=None) -> Generator[list[IPNode],None,None]:
        max_level_nodes = dao.seleccionarCoincidencia(IPNode,'max_child_level_by_parent',parent_ip)
        if not max_level_nodes:
            return []
        if depth > max_level_nodes[0].max_level:
            depth = max_level_nodes[0].max_level
        for level in range(0,depth+1):
            yield dao.seleccionarCoincidencia(IPNode,'child_level',level)

    def select_all_ports(self,dao:GenericDAO=None) -> list[Ports]:
        return dao.seleccionar(Ports)
    def select(self,data,dao:GenericDAO=None):
        nodes = dao.seleccionar(data)
        return nodes
    def delete_ip(self,ip_id:int,dao:GenericDAO=None):
        try:
            data =dao.seleccionarPorId(IPNode,ip_id)
            if not data:
                raise ValueError(f"No IPNode found with id {ip_id}")
            dao.eliminar(data,data.id)
        except Exception as e:
            log.error(f"[-] error deleting node \n {e}")
    def update_ip(self,ip_id:int,new_ip:IPNode,dao:GenericDAO=None):
        try:
            data =dao.seleccionarPorId(IPNode,ip_id)
            if not data:
                raise ValueError(f"No IPNode found with id {ip_id}")
            dao.actualizar(new_ip,new_ip.id)
        except Exception as e:
            log.error(f"[-] error updating node \n {e}")


def main():
    dao = GenericDAO()
    crud = CRUD_GATHERINGDB(dao)
    ln_ip = crud.show_all_data(IPNode,dao=dao)
    ln = crud.show_all_data(Ports,dao=dao)
    
    for x in crud.select(IPNode,dao=dao):
        print(x.id)
        crud.delete_ip(x.id, dao=dao)
    
    crud.insert_ip('192.168.2.1',os.getcwd(),'', dao=dao)
    crud.insert_ip('192.168.2.5',os.getcwd(),'', dao=dao)
    #crud.insert_port_node(1, 8080, dao=dao)
    crud.show_all_data(IPNode,dao=dao)
    up:IPNode = crud.select_ip_by_field('ip', '192.168.2.1', dao=dao)[0]
    
    up.parent_ip = '192.168.20.2'
    print(up)
    crud.update_ip(up.id,up,dao=dao)
    

if __name__ == '__main__':
    DatabaseInitializer.initialize_db(dao=GenericDAO())
    
    main()
# posible feature
# agregar un generador de nombres aleatorios para las direcciones IP y estos nombres pasarlos
# a una funcion que genere vareables de entorno para que se pueda facilmente se;alar la direccion IP 
