# ÆON-Link v0.3.0 — Comunicación semántica entre inteligencias artificiales

**Estado: experimental, pre-alfa. Licencia MIT.** No es un estándar universal ni existe evidencia de que una IA comprenda realmente a otra a través de este protocolo.

[Documentación técnica en inglés](README.md)

## Mejoras implementadas

- **Formato reproducible Python/Node.js:** JSON UTF-8 con claves ASCII, cadenas Unicode y enteros seguros; rechaza números de punto flotante, claves ambiguas y representaciones no canónicas. No es RFC 8785.
- **Autenticación opcional HMAC-SHA256:** firma el mensaje junto con su metadato de validez temporal y vincula la clave a un emisor previamente confiado.
- **Prevención de repetición persistente:** usa SQLite y transacciones para identificar mensajes repetidos incluso luego de reiniciar el proceso.
- **Validación de evidencia:** verifica que los bytes entregados coincidan con un hash SHA-256. Esto no prueba la verdad del contenido.
- **Pruebas:** se incluyen tests Python y Node, con casos negativos para alteraciones, vencimiento e identidad.

## Cómo probar el repositorio

```bash
python -m unittest discover -s tests -v
node --test js/*.test.mjs
```

**Alcance de GitHub:** implementación autónoma reducida. El paquete ampliado v0.3.0 desarrollado durante la investigación contiene un SDK Python con JSON Schema y más pruebas; por ahora ambos no son distribuciones idénticas.

**Limitaciones:** no conecta modelos comerciales, no opera sistemas, no valida la procedencia real de las fuentes y no reemplaza A2A, MCP, TLS ni OAuth. La firma no concede permisos: la autorización depende del sistema receptor.

## Próxima investigación

Importar al repositorio toda la versión ampliada, completar pruebas cruzadas de conformidad, integrar agentes reales usando sus APIs, medir errores semánticos, establecer revisión independiente y gobernanza abierta.
