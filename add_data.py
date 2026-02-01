from launch import build_core_stack
dao, crud, core, cmd, generic = build_core_stack()

# Agregar IPs de ejemplo
crud.insert_ip("192.168.1.1", "/path/to/192.168.1.1", "", 0, dao=dao)
crud.insert_ip("192.168.1.100", "/path/to/192.168.1.100", "192.168.1.1", 1, dao=dao)

# Agregar puertos
ip_nodes = crud.select_all_ips(dao=dao)
for ip in ip_nodes:
    if ip.ip == "192.168.1.1":
        crud.insert_port_node(ip.id, 22, "ssh", dao=dao)
        crud.insert_port_node(ip.id, 80, "http", dao=dao)
    elif ip.ip == "192.168.1.100":
        crud.insert_port_node(ip.id, 3306, "mysql", dao=dao)

print("IPs and ports added")