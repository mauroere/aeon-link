# ÆON-Link — Protocolo semántico experimental entre agentes

Este repositorio contiene una implementación mínima en Python del intercambio de objetivos, estados epistémicos, referencias a evidencias, negociación de capacidades y autorización del receptor.

**Estado:** prototipo. No se comprobó comprensión semántica entre modelos de IA reales. Las referencias de evidencia no prueban que una fuente sea verdadera. La política local requiere autenticación externa. Los hashes no prueban comprensión.

## Prueba rápida
```bash
python -m unittest discover -s tests -v
```

La versión extendida v0.2.0 con SDK Python, Node.js, especificación y pruebas cruzadas se proporciona también como paquete ZIP en la conversación donde se desarrolló. Esta publicación inicial contiene una implementación de referencia reducida, no todo el paquete extendido.

## Objetivos
1. Contrato formal de intercambio entre agentes.
2. Adopción como capa semántica opcional encima de A2A/MCP.
3. Pruebas con múltiples proveedores de IA.
4. Seguridad, autoría, procedencia verificable y benchmarks independientes.

Licencia MIT.
