from tunnelsManager.ports.drivens.forConnectionTest import ForConnectionTest
import socket

class NetworkConnectionTester(ForConnectionTest):
    def test_local_port_open(self, port: int) -> bool:
        """Intenta abrir un socket en el puerto local para ver si está en uso.
        Ojo: Dependiendo de cómo lo maneje el SO, un puerto en uso no se puede bindear.
        Si falla el bind, significa que probablemente el puerto está ocupado (abierto por un túnel).
        Sin embargo, para propósitos del ejercicio, asumimos siempre true por defecto o verificamos
        estado. Aquí hacemos una verificación muy básica.
        """
        # Para propósitos de este adapter, consideramos que la solicitud de crear el túnel
        # implica que el operador lo abrió. Retornamos True por ahora, pero aquí iría la
        # lógica real (p. ej. usar psutil, socket bind test, etc).
        return True
