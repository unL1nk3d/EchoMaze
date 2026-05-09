import os
from typing import Generator
from GATHERINGDB.dao import GenericDAO, Transaction
from GATHERINGDB.model import IPNode, Ports, Actions, Artifacts
from GATHERINGDB.init_db import DatabaseInitializer
from GATHERINGDB.log import log


class CRUD_GATHERINGDB:
    def __init__(self, dao: GenericDAO = None):
        self.dao = dao

    def check_field_n_value(self, field: str, value: str):
        if not (isinstance(field, str) and isinstance(value, str)):
            raise ValueError("Field and value must be strings")

    def select_ip_by_field(self, field: str, value: str, dao: GenericDAO = None) -> list[IPNode]:
        self.check_field_n_value(field, value)
        try:
            if dao is None: dao = self.dao
            nodes = dao.seleccionarCoincidencia(IPNode, field, value)
            return nodes
        except Exception as e:
            log.error(f"[-] error selecting nodes by field \n {e}")
            return []

    def select_port_by_field(self, field: str, value: str, dao: GenericDAO = None) -> list[Ports]:
        self.check_field_n_value(field, value)
        try:
            if dao is None: dao = self.dao
            node = dao.seleccionarCoincidencia(Ports, field, value)
            return node
        except Exception as e:
            log.error(f"[-] error selecting nodes by field \n {e}")
            return []

    def insert_port_node(self, ip_id, ports, service_name='unknown', dao: GenericDAO = None):
        try:
            if dao is None: dao = self.dao
            data = dao.seleccionarPorId(IPNode, ip_id)
            if not data:
                raise ValueError(f"No IPNode found with id {ip_id}")
            ports = Ports(id=0, port=ports, service_name=service_name, ip=data.ip)
            dao.insertar(ports)
        except Exception as e:
            log.error(f"[-] error inserting node \n {e}")

    def insert_ip(self, ip: str, current_path: str, parent_ip: str, child_level: int = 0, dao: GenericDAO = None):
        if dao is None: dao = self.dao
        node = IPNode(id=0, ip=ip, parent_ip=parent_ip, child_level=child_level, path=current_path)
        dao.insertar(node)

    def show_all_data(self, data, dao: GenericDAO = None):
        if dao is None: dao = self.dao
        nodes = dao.seleccionar(data)
        for node in nodes:
            print(node)
        return len(nodes)

    def select_all_ips(self, dao: GenericDAO = None) -> list[IPNode]:
        if dao is None: dao = self.dao
        return dao.seleccionar(IPNode)

    def select_depth_ips(self, depth: int, dao: GenericDAO = None) -> list[IPNode]:
        if dao is None: dao = self.dao
        return dao.seleccionarCoincidencia(IPNode, 'child_level', str(depth))

    def select_ip_parents(self, parent_ip: str, depth: int, dao: GenericDAO = None) -> Generator[list[IPNode], None, None]:
        if dao is None: dao = self.dao
        max_level_nodes = dao.seleccionarCoincidencia(IPNode, 'max_child_level_by_parent', parent_ip)
        if not max_level_nodes:
            return []
        if depth > max_level_nodes[0].max_level:
            depth = max_level_nodes[0].max_level
        for level in range(0, depth + 1):
            yield dao.seleccionarCoincidencia(IPNode, 'child_level', str(level))

    def select_all_ports(self, dao: GenericDAO = None) -> list[Ports]:
        if dao is None: dao = self.dao
        return dao.seleccionar(Ports)

    def insert_action(self, action: Actions, dao: GenericDAO = None) -> bool:
        try:
            if dao is None: dao = self.dao
            if getattr(action, 'noise_score', 0.0) == 0.0:
                try:
                    from cheatIngestor.api import get_noise_estimate_for_command
                    from core.entropy import get_event_probability, calculate_noise_score
                    estimate = get_noise_estimate_for_command(action.command_template, dao=dao)
                    class _DummyEvent: pass
                    dummy_event = _DummyEvent()
                    dummy_event.command_template = action.command_template
                    dummy_event.noise_estimate = estimate
                    historial = self.select_all_actions(dao=dao)
                    prob = get_event_probability(dummy_event, historial)
                    action.noise_score = calculate_noise_score(prob)
                except Exception as ex:
                    log.error(f"[-] Error calculating noise_score: {ex}")
                    action.noise_score = 0.0
            dao.insertar(action)
            return True
        except Exception as e:
            log.error(f"[-] error inserting action: {str(e)}")
            return False

    def select_all_actions(self, dao: GenericDAO = None) -> list[Actions]:
        try:
            if dao is None: dao = self.dao
            return dao.seleccionar(Actions)
        except Exception as e:
            log.error(f"[-] error selecting actions: {str(e)}")
            return []

    def select_actions_by_field(self, field: str, value: str, dao: GenericDAO = None) -> list[Actions]:
        try:
            if dao is None: dao = self.dao
            return dao.seleccionarCoincidencia(Actions, field, value)
        except Exception as e:
            log.error(f"[-] error selecting actions by {field}: {str(e)}")
            return []

    def select_actions_by_node_id(self, node_id: int, dao: GenericDAO = None) -> list[Actions]:
        return self.select_actions_by_field('node_id', str(node_id), dao)

    def insert_artifact(self, artifact: Artifacts, dao: GenericDAO = None) -> bool:
        try:
            if dao is None: dao = self.dao
            dao.insertar(artifact)
            return True
        except Exception as e:
            log.error(f"[-] error inserting artifact: {str(e)}")
            return False

    def select_artifacts_by_node_id(self, node_id: int, dao: GenericDAO = None) -> list[Artifacts]:
        try:
            if dao is None: dao = self.dao
            return dao.seleccionarCoincidencia(Artifacts, 'node_id', str(node_id))
        except Exception as e:
            log.error(f"[-] error selecting artifacts by node_id: {str(e)}")
            return []

    def select(self, data, dao: GenericDAO = None):
        if dao is None: dao = self.dao
        return dao.seleccionar(data)

    def delete_ip(self, ip_id: int, dao: GenericDAO = None):
        try:
            if dao is None: dao = self.dao
            data = dao.seleccionarPorId(IPNode, ip_id)
            if not data:
                raise ValueError(f"No IPNode found with id {ip_id}")
            dao.eliminar(data, data.id)
        except Exception as e:
            log.error(f"[-] error deleting node \n {e}")

    def update_ip(self, ip_id: int, new_ip: IPNode, dao: GenericDAO = None):
        try:
            if dao is None: dao = self.dao
            data = dao.seleccionarPorId(IPNode, ip_id)
            if not data:
                raise ValueError(f"No IPNode found with id {ip_id}")
            dao.actualizar(new_ip, new_ip.id)
        except Exception as e:
            log.error(f"[-] error updating node \n {e}")


def main():
    dao = GenericDAO()
    crud = CRUD_GATHERINGDB(dao)
    ln_ip = crud.show_all_data(IPNode, dao=dao)
    ln = crud.show_all_data(Ports, dao=dao)
    for x in crud.select(IPNode, dao=dao):
        print(x.id)
        crud.delete_ip(x.id, dao=dao)
    crud.insert_ip('192.168.2.1', os.getcwd(), '', dao=dao)
    crud.insert_ip('192.168.2.5', os.getcwd(), '', dao=dao)
    crud.show_all_data(IPNode, dao=dao)
    up: IPNode = crud.select_ip_by_field('ip', '192.168.2.1', dao=dao)[0]
    up.parent_ip = '192.168.20.2'
    print(up)
    crud.update_ip(up.id, up, dao=dao)


if __name__ == '__main__':
    DatabaseInitializer.initialize_db(dao=GenericDAO())
    main()
