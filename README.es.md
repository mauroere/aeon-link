# ÆON-Link 0.4.0 — Interoperabilidad semántica experimental entre IA

**Estado real:** prototipo técnico reproducible. Todavía no es un estándar, no conecta con ChatGPT/Claude/Gemini, ni comprueba la veracidad de las fuentes o la identidad criptográfica de los agentes.

## ¿Qué intenta resolver?

Que dos agentes IA intercambien objetivos, restricciones, hipótesis y referencias a evidencia mediante un contrato semántico conocido. Si no comparten un significado compatible, el intercambio debe fallar en lugar de fingir compatibilidad.

## ¿Qué se puede probar hoy?

- Negociación de versión, ontología y funciones entre dos agentes simulados.
- Esquema JSON Schema estricto y comprobación de referencias entre afirmaciones y evidencias.
- Acuse de recepción del objetivo y restricciones mediante hashes reproducibles en Python y Node.js para los casos de prueba.
- Política local de autorización que no concede permisos a partir de lo escrito en el mensaje.
- Conversión de los datos del protocolo al campo estructurado de A2A o al de resultados de herramientas MCP. **No es una integración completa de red con esos protocolos**.
- 35 pruebas Python, 8 pruebas Node.js y un intercambio entre ambos entornos.

## Uso

Requiere Python 3.10+ y Node.js 22+ (Node solo para pruebas cruzadas).

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/demo.py
node --test js/test.mjs
node js/create-ack.mjs < fixtures/python-task.json > node-ack.json
python examples/check_node_ack.py node-ack.json
```

Si no se pueden instalar dependencias por falta de Internet pero ya está instalado `jsonschema`, usar `PYTHONPATH=src` en los comandos Python (Linux/macOS). En PowerShell: `$env:PYTHONPATH='src'`.

## Qué falta para conseguir una adopción real

- Adaptadores completos, utilizando SDK oficiales de modelos y protocolos.
- Identidad criptográfica, auditoría, validación de fuentes y controles operativos.
- Compatibilidad semántica comprobada con distintas IA reales, no solo intercambios deterministas.
- Pruebas de eficiencia y precisión contra los protocolos actuales.
- Publicar en un repositorio independiente, discutir la especificación e incorporar contribuidores externos.

El proyecto se distribuye con licencia MIT. Consultar [README.md](README.md), [especificación técnica](docs/SPEC.md) y [riesgos de seguridad](docs/SECURITY.md).

## Novedades de seguridad v0.3.0

- Firmas HMAC-SHA256 en Python y Node.js sobre JSON canónico restringido (no RFC 8785), vinculadas a la identidad confiada por el receptor.
- Rechazo de mensajes alterados, vencidos o enviados con claves no reconocidas.
- Registro SQLite para evitar repeticiones incluso después de reinicios.
- Pruebas bidireccionales de firmas Python ↔ Node.js y contenido Unicode.
- Verificación opcional del hash SHA-256 de bytes de evidencia aportados localmente.

No hay conexión a IA comerciales, control de infraestructura ni prueba de comprensión semántica real. Firmar un mensaje no equivale a autorizar una acción.


## Novedad 0.4: contratos semánticos ejecutables

Dos agentes pueden intercambiar un contrato con condiciones **obligatorias**, **prohibidas** y resultados **desconocidos**. El sistema genera automáticamente situaciones contrafácticas; otro agente debe clasificar cada caso como `satisfied`, `violated` o `incomplete`. Se comprueban identificadores, nonce y huella del contrato. **No equivale a demostrar comprensión cognitiva**.

También se incorporó un grafo de evidencias con vínculos de apoyo, refutación y dependencia. Detecta ciclos, referencias inexistentes y contradicciones potenciales. Una fuente externa debe corroborar la evidencia: declararla `fact` no la convierte en verdadera.

### Pruebas

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
node --test js/*.test.mjs
```

Más detalles en [la especificación semántica](docs/SEMANTIC_CONFORMANCE.md).

## SDK 0.5.0 (formato de mensajes 0.4.0)

La versión 0.5.0 agrega recepción segura de mensajes firmados, validación del
destinatario, política local de autorización y protección contra reenvíos.
En Node el host debe proporcionar un registro antirrepetición atómico y
persistente, y el SDK espera su finalización.

También incorpora retos semánticos contrafácticos e invariantes, recibos de
decisión que pueden comprobarse en Python y Node, y pruebas diferenciales de
compatibilidad. La auditoría descubrió once discrepancias Python/Node en
121 casos, posteriormente corregidas en la versión local.

**No significa que la IA comprenda realmente una intención ni que el proyecto
sea superior a A2A o MCP.** Las pruebas son principalmente deterministas.
Consultá `docs/INBOUND_SECURITY.md` y `docs/DECISION_RECEIPTS.md`.

## SDK v0.6.0 — Seguridad externa e interoperabilidad real

Se implementaron adaptadores **opcionales** para las APIs comerciales de OpenAI, Anthropic y Gemini, pruebas con respuestas simuladas y una herramienta para ensayos comparativos con dos formatos de mensajes. Las llamadas reales **no se ejecutaron** porque no hay claves API autorizadas disponibles. Requieren ejecutar expresamente `examples/live_provider_benchmark.py --i-accept-api-costs`; pueden ocasionar cargos.

Se agregó CodeQL (análisis estático automatizado de GitHub), Dependabot y un modelo para solicitar una auditoría humana externa. **El análisis automatizado no equivale a una auditoría independiente concluida**. La adopción universal y la superioridad frente a soluciones existentes permanecen **sin demostrar**.

Se corrigió una fuga de conexiones SQLite y se bloquearon las redirecciones HTTP de los adaptadores para evitar redirigir credenciales.

[Estado y próximos experimentos](docs/INDEPENDENT_REVIEW_AND_ADOPTION.md) · [Política de vulnerabilidades](SECURITY.md)
