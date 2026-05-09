import math
from collections import Counter

# Tabla de entropía por tipo de dato en bits/byte
ENTROPY_DATA_TYPES = {
    'texto plano': 4.1,
    'codigo fuente': 5.2,
    'imagenes jpeg': 7.6,
    'datos cifrados': 8.9,
    'base64 encode': 6.0,
    'post compresion data': 6.8
}

def get_event_probability(evento, historial):
    """
    Calcula la probabilidad de detección de un evento (comando).
    Si el evento (Template/Acción) ya tiene un `noise_estimate` válido, lo usa.
    De lo contrario, estima la probabilidad en base a su frecuencia en el historial.
    """
    # Si noise_estimate viene en el evento (por cheatIngestor), usalo
    if hasattr(evento, 'noise_estimate') and evento.noise_estimate is not None and evento.noise_estimate > 0:
        return evento.noise_estimate

    # Si no, estimar por frecuencia en el historial
    total = len(historial)

    # Asumimos que evento tiene un atributo 'comando' o 'command_template'
    comando = getattr(evento, 'command_template', getattr(evento, 'comando', str(evento)))

    if total == 0:
        return 1.0

    freq = sum(1 for e in historial if getattr(e, 'command_template', getattr(e, 'comando', str(e))) == comando)

    prob = freq / total if total > 0 else 1.0
    return prob

def calcular_entropia(historial):
    """
    Aplica la definición termodinámica (entropía): H(X) = -sumatoria(p(i)*log_2(P(i)))
    """
    total = len(historial)
    if total == 0:
        return 0.0

    counter = Counter(getattr(e, 'command_template', getattr(e, 'comando', str(e))) for e in historial)
    entropia = 0.0

    for count in counter.values():
        p_i = count / total
        entropia -= p_i * math.log2(p_i)

    return entropia

def puede_ocultar(portador_bits, entropia_portador, info_bits, entropia_info):
    """
    Algoritmo para validación de camuflaje (steganografía):
    La entropía del portador debe ser >= entropía del mensaje a ocultar.
    """
    capacidad = portador_bits * entropia_portador
    necesario = info_bits * entropia_info
    return capacidad >= necesario

def evaluate_exfiltration(info_type, info_size_bytes, portador_type, portador_size_bytes):
    """
    Evalúa si un método de exfiltración es válido.
    Devuelve un tupla (bool, str) indicando si es válido y un mensaje de advertencia.
    """
    if info_type not in ENTROPY_DATA_TYPES:
        return False, f"Tipo de información desconocido: {info_type}"
    if portador_type not in ENTROPY_DATA_TYPES:
        return False, f"Tipo de portador desconocido: {portador_type}"

    entropia_info = ENTROPY_DATA_TYPES[info_type]
    entropia_portador = ENTROPY_DATA_TYPES[portador_type]

    # Shannon limit check
    if portador_size_bytes < info_size_bytes:
        return False, "Límite de Shannon excedido: La longitud del portador/clave debe ser igual o mayor al mensaje."

    info_bits = info_size_bytes * 8
    portador_bits = portador_size_bytes * 8

    es_valido = puede_ocultar(portador_bits, entropia_portador, info_bits, entropia_info)

    if not es_valido:
        return False, "La capacidad entrópica del portador es insuficiente para ocultar la información."

    return True, "Camuflaje válido. El portador tiene suficiente entropía."

def calculate_noise_score(probability):
    """
    Ruido: -log₂(P(evento))
    """
    if probability <= 0 or probability > 1.0:
        probability = 1.0
    return -math.log2(probability) if probability > 0 and probability < 1.0 else 0.0


def get_entropy_warning(entropia):
    """
    Devuelve un mensaje de advertencia basado en el nivel de entropía global.
    A mayor entropía, mayor probabilidad de detección en el sistema.
    """
    if entropia < 2.0:
        return "Baja entropía. Sistema poco ruidoso. (Poco detectable)"
    elif entropia < 4.0:
        return "Media entropía. Actividad mixta detectada. (Moderadamente detectable)"
    else:
        return "ALTA ENTROPÍA. Advertencia: El sistema exhibe alta variabilidad de eventos, alta probabilidad de detección."
