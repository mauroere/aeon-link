# ÆON-Link — Interoperabilidad semántica experimental entre IA

**SDK 0.6.0 · Formato de mensajes 0.4.0 · MIT · pre-alfa**

[Documentación técnica](README.md) · [Especificación](docs/SPEC.md) · [Seguridad](SECURITY.md) · [Estado de auditoría y adopción](docs/INDEPENDENT_REVIEW_AND_ADOPTION.md) · [Historial](CHANGELOG.md)

ÆON-Link ofrece una **capa opcional para intercambiar información semántica** entre agentes de inteligencia artificial: objetivos, restricciones, incertidumbre, referencias a evidencias y condiciones verificables. Complementa A2A y MCP; **no los reemplaza**. No constituye un estándar universal ni está demostrado que mejore la comprensión de modelos comerciales.

## Funciones comprobables

- Implementaciones Python y Node.js: validaciones, intercambio estructurado, formato JSON reproducible, negociación de versiones y ontologías.
- Firmas HMAC opcionales y protección de mensajes contra caducidad y repetición. La autorización depende de políticas locales, no de permisos autodeclarados por una IA.
- Contratos semánticos ejecutables, retos contrafácticos, recibos de decisiones y grafos de evidencias. **Validar la estructura de una prueba no confirma que sea verdadera.**
- Adaptadores de carga útil para A2A y resultados MCP. **No son servidores A2A/MCP completos.**
- Conectores HTTPS **opcionales** para las APIs oficiales de OpenAI, Anthropic y Gemini, con respuestas simuladas en las pruebas automáticas.
- Herramientas optativas para comparar dos formatos de mensajes y para transferir una tarea restringida del modelo A al modelo B; sin ejecutar acciones sobre sistemas externos.
- CodeQL (análisis estático automatizado), Dependabot, documentación de vulnerabilidades y solicitud de revisión humana externa.

## Instalar y ejecutar pruebas

Requiere Python 3.10+ y Node.js 22+ para las pruebas cruzadas.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
node --test js/*.test.mjs js/test.mjs
```

Sin acceso a Internet, si `jsonschema` ya está instalado, podés ejecutar las pruebas Python con `PYTHONPATH=src` en Linux/macOS, o `$env:PYTHONPATH='src'` en PowerShell.

## Conectar modelos comerciales reales

Los conectores están desarrollados, pero **no se realizaron llamadas reales** durante esta versión porque no había claves API autorizadas. Es necesario disponer de claves propias en variables de entorno (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`), modelos habilitados y ejecutar expresamente las pruebas. Pueden generarse costos.

```sh
python examples/live_provider_benchmark.py --provider openai --model <MODELO_HABILITADO> --limit 12 --i-accept-api-costs
python examples/live_model_relay.py --provider-a openai --model-a <MODELO_A> --provider-b anthropic --model-b <MODELO_B> --action write --i-accept-api-costs
```

La segunda prueba evalúa si el modelo B respeta la prohibición de realizar cambios; **no ejecuta** ninguna acción real. No compartas claves en conversaciones, repositorios ni incidencias públicas.

## Los cuatro objetivos de investigación

| Objetivo | Estado verificable |
| --- | --- |
| Auditoría de seguridad independiente | **Pendiente de especialista humano externo**. CodeQL es análisis automatizado, no auditoría humana. |
| Comunicación entre IA comerciales | **Código listo para pruebas autorizadas**, pero sin llamadas reales ejecutadas. |
| Superioridad frente a alternativas | **No demostrada**. A2A/MCP son tecnologías complementarias, no un reemplazo directo. |
| Adopción como protocolo universal | **No lograda**. La publicación del código no implica adopción ni estandarización. |

Se corrigieron errores concretos, incluidos cierres de conexiones SQLite y bloqueo de redirecciones HTTP con claves API. El proyecto sigue siendo experimental; no debe utilizarse como barrera única de seguridad de un sistema.

[Estado ampliado y criterios para nuevas pruebas](docs/INDEPENDENT_REVIEW_AND_ADOPTION.md).