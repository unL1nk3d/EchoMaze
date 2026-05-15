# EchoMaze Tunnels Manager API

## Overview

The `tunnelsManager` module provides functionalities for managing network tunnels and implants during penetration testing. This API acts as a unified facade for both `TunnelsUseCase` and `ImplantsUseCase`, making it easy for external clients (like LLMs or MCP servers) to interact with the system.

## Key Features

- **Tunnel Lifecycle Management**: Create, setup, and manage the phase of network tunnels.
- **Implant Management**: Create and list implants, and generate payloads for different platforms (Python, PowerShell, Stagers).
- **Health Monitoring**: Check tunnel status and connectivity.
- **Statistics & Entropy**: Get global tunnel statistics and evaluate the entropy of specific tunnels to detect potential exfiltration patterns.
- **Discovery Mechanism**: Self-documenting API that can list its own functions and signatures.

## Programmatic Usage

### Getting the API instance

```python
from tunnelsManager import get_tunnels_api

# Initialize the API (uses GenericDAO by default)
api = get_tunnels_api()
```

### Discovery

LLMs can use the `list_available_functions()` method to discover what they can do:

```python
functions = api.list_available_functions()
for func in functions:
    print(f"Name: {func['name']}")
    print(f"Signature: {func['signature']}")
    print(f"Description: {func['description']}")
    print("-" * 20)
```

### Managing Tunnels

```python
# Create a new tunnel with a predefined data type for automatic entropy calculation
tunnel = api.create_tunnel(
    source_ip="192.168.1.10", 
    local_port=8080, 
    tunnel_type="HTTP",
    data_type="imagenes jpeg"
)

# If data_type is not provided, it will fallback to a default mapping based on tunnel_type
tunnel_default = api.create_tunnel(source_ip="192.168.1.10", local_port=443, tunnel_type="Shadowsocks")

# Advance tunnel phase
api.advance_tunnel_phase(tunnel.id)

# Get all tunnels
all_tunnels = api.get_all_tunnels()

# Get stats
stats = api.get_tunnel_stats()
print(f"Active Tunnels: {stats['active']}")
```

### Managing Implants

```python
# Create an implant
implant = api.create_implant(name="RevShell", implant_type="Python", payload="...")

# Generate a payload
payload = api.generate_payload(implant_type="Python", listener_ip="10.10.10.10", listener_port=4444)
```

## API Reference

The `TunnelsManagerAPI` class proxies the following methods:

### Tunnels
- `create_tunnel(...)`
- `advance_tunnel_phase(tunnel_id)`
- `get_all_tunnels()`
- `get_tunnel_stats()`
- `evaluate_tunnel_entropy(tunnel_id)`
- `check_tunnels_health()`
- ... and more.

### Implants
- `create_implant(...)`
- `list_implants()`
- `generate_payload(implant_type, listener_ip, listener_port)`
- ... and more.

## Testing

To run the tests for the Tunnels API:

```bash
python -m unittest test/test_tunnels_api.py
```
