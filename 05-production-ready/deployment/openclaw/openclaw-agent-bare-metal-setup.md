# Cómo desplegué OpenClaw en un servidor Debian bare-metal

**Entorno:** Debian Trixie — bare-metal Celeron
**Versión de OpenClaw:** 2026.5.7
**Modelo de IA:** OpenCode Go (DeepSeek V4 Pro como primario)
**Interfaz principal:** Telegram
**Última actualización:** Mayo 2026 — migración desde 2026.3.13

---

Tengo un servidor viejo con procesador Celeron corriendo Debian Trixie en bare-metal. La idea era convertirlo en un **agente asíncrono** disponible 24/7: yo le mando tareas por Telegram desde cualquier parte y él las ejecuta mientras yo hago otra cosa. Esto es lo que hice para lograrlo.

---

## 1. Primero: el sandbox de seguridad

No quería que el agente tuviera acceso libre al sistema. Lo más limpio que encontré fue correrlo bajo un usuario sin `sudo`, completamente aislado.

```bash
# Crear el usuario restringido
sudo adduser --disabled-password --gecos "" openclaw_user

# Bloquear mi carpeta personal por las dudas
sudo chmod 700 /home/[mi-usuario]
```

### El dolor de Node.js en Debian

OpenClaw requiere Node.js 22+. Debian tenía cacheada la v20 de algún repositorio viejo y me daba conflictos. Tuve que purgar todo y forzar la instalación desde el repositorio oficial:

```bash
sudo apt-get purge -y nodejs libnode-dev
sudo apt-get autoremove -y

curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

node -v  # Verificar que sea 22.x o superior
```

---

## 2. Instalación de OpenClaw (dentro del sandbox)

Todo lo que sigue lo hice **como `openclaw_user`**, nunca como mi usuario principal.

```bash
sudo su - openclaw_user

# Configurar npm para instalaciones locales (sin necesitar sudo)
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Instalar OpenClaw (siempre la última versión)
npm install -g openclaw@latest
```

### Setup inicial (crítico)

Antes de levantar cualquier servicio, hay que correr el asistente de configuración. Esto crea la estructura de carpetas que OpenClaw necesita para funcionar:

```bash
openclaw setup
```

---

## 3. Servicio systemd para que corra 24/7

Para que el agente sobreviva reinicios y caídas, lo convertí en un daemon. Este paso lo hice desde mi usuario principal (con `sudo`):

```bash
sudo nano /etc/systemd/system/openclaw.service
```

```ini
[Unit]
Description=OpenClaw AI Agent Daemon
After=network.target

[Service]
Type=simple
User=openclaw_user
WorkingDirectory=/home/openclaw_user
EnvironmentFile=/home/openclaw_user/.openclaw/.env
# IMPORTANTE: en versiones recientes usar 'gateway --force', no 'start' ni 'daemon'
ExecStart=/home/openclaw_user/.npm-global/bin/openclaw gateway --force
Restart=on-failure
RestartSec=10
# Optimizaciones para hardware limitado (Celeron/Pi/VM) — recomendado por openclaw doctor
Environment=NODE_COMPILE_CACHE=/var/tmp/openclaw-compile-cache
Environment=OPENCLAW_NO_RESPAWN=1

[Install]
WantedBy=multi-user.target
```

Crear el directorio de cache y aplicar:

```bash
sudo mkdir -p /var/tmp/openclaw-compile-cache
sudo chown openclaw_user:openclaw_user /var/tmp/openclaw-compile-cache

sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw
```

---

## 4. Conectar Telegram como interfaz de chat

Creé un bot con **@BotFather** en Telegram y copié el token. Después usé el asistente interactivo de canales:

```bash
# Como openclaw_user
openclaw channels add
```

El flujo del asistente:
1. ¿Configurar canales ahora? → `Yes`
2. Select a channel → `Telegram`
3. Telegram account → `Add a new account` → `default (primary)`
4. Provide token → pegar el token del bot

Después vinculé el canal al agente principal y reinicié:

```bash
sudo systemctl restart openclaw
```

### Pairing: desbloquear el bot

Por defecto, OpenClaw ignora mensajes directos por seguridad. Al escribirle "Hola" al bot en Telegram, me respondió con un **Pairing code**. Lo aprobé desde la terminal:

```bash
sudo -u openclaw_user /home/openclaw_user/.npm-global/bin/openclaw pairing approve telegram [EL-CODIGO]
```

### Command owner (importante para seguridad)

El pairing solo permite hablar con el bot. Para poder ejecutar comandos privilegiados desde Telegram (`/config`, `/diagnostics`, aprobaciones de exec), hay que configurar el owner. Obtén tu Telegram ID hablándole a `@userinfobot`:

```bash
# Como openclaw_user
openclaw config set commands.ownerAllowFrom '["telegram:TU_ID_NUMERICO"]'
exit
sudo systemctl restart openclaw
```

Sin esto, nadie tiene privilegios de owner aunque haya hecho pairing.

---

## 5. OpenCode Go: configuración del provider y modelos

OpenCode Go es una suscripción que da acceso a modelos open source de calidad. El catálogo completo disponible en 2026.5.7:

| Model ref | Modelo | Fortaleza |
|---|---|---|
| `opencode-go/deepseek-v4-pro` | DeepSeek V4 Pro | **Primario recomendado.** Coding avanzado, agentes, 80.6% SWE-bench, 1M contexto |
| `opencode-go/deepseek-v4-flash` | DeepSeek V4 Flash | Coding rápido y económico |
| `opencode-go/kimi-k2.6` | Kimi K2.6 | 256K contexto, documentos largos, multimodal — ⚠️ bug: thinking mode se activa siempre en subagentes (error 400), no usar como primario |
| `opencode-go/kimi-k2.5` | Kimi K2.5 | Frontend, contexto 256K, multimodal |
| `opencode-go/minimax-m2.7` | MiniMax M2.7 | Coding general, última generación |
| `opencode-go/minimax-m2.5` | MiniMax M2.5 | Coding general (SWE-Bench 80.2%) |
| `opencode-go/glm-5.1` | GLM-5.1 | Razonamiento matemático, última generación |
| `opencode-go/glm-5` | GLM-5 | Razonamiento matemático |
| `opencode-go/mimo-v2-pro` | MiMo V2 Pro | Razonamiento multimodal |
| `opencode-go/mimo-v2-omni` | MiMo V2 Omni | Multimodal general |
| `opencode-go/qwen3.6-plus` | Qwen3.6 Plus | Coding y razonamiento, buen tool-calling |
| `opencode-go/qwen3.5-plus` | Qwen3.5 Plus | Coding general |

### Por qué el `.env` va en `~/.openclaw/.env`

OpenClaw tiene un orden de precedencia estricto para variables de entorno. La ubicación correcta para credenciales en un servicio systemd es `~/.openclaw/.env`, **no** `~/.env`. El `EnvironmentFile` del service debe apuntar ahí.

### Onboarding de OpenCode Go

```bash
sudo su - openclaw_user
openclaw onboard --auth-choice opencode-go
```

El asistente detecta el config existente. Seleccionar:
- Config handling → `Use existing values`
- Web search → `Skip for now` (se configura por separado)
- Skills → `Skip for now`

### Agregar todos los modelos al allowlist

**IMPORTANTE:** `agents.defaults.models` actúa como allowlist. Solo los modelos listados ahí son accesibles desde `/model` y sesiones. Hay que agregarlos manualmente al `openclaw.json` ya que el flag `--merge` del CLI puede no estar disponible en todas las versiones:

```bash
nano ~/.openclaw/openclaw.json
```

La sección `agents.defaults.models` debe quedar así:

```json
"models": {
  "opencode-go/kimi-k2.6": { "alias": "Kimi-Pro" },
  "opencode-go/kimi-k2.5": { "alias": "Kimi" },
  "opencode-go/glm-5": { "alias": "GLM" },
  "opencode-go/glm-5.1": { "alias": "GLM-5.1" },
  "opencode-go/minimax-m2.5": { "alias": "MiniMax" },
  "opencode-go/minimax-m2.7": { "alias": "MiniMax-Pro" },
  "opencode-go/deepseek-v4-pro": { "alias": "DeepSeek-Pro" },
  "opencode-go/deepseek-v4-flash": { "alias": "DeepSeek-Flash" },
  "opencode-go/mimo-v2-pro": { "alias": "MiMo-Pro" },
  "opencode-go/mimo-v2-omni": { "alias": "MiMo-Omni" },
  "opencode-go/qwen3.5-plus": { "alias": "Qwen3.5" },
  "opencode-go/qwen3.6-plus": { "alias": "Qwen3.6" }
}
```

Siempre validar el JSON antes de reiniciar:

```bash
cat ~/.openclaw/openclaw.json | python3 -m json.tool > /dev/null && echo "JSON válido"
```

### Setear el modelo primario

```bash
openclaw config set agents.defaults.model.primary "opencode-go/deepseek-v4-pro"
exit
sudo systemctl restart openclaw
```

Verificar en los logs:

```bash
sudo journalctl -u openclaw -f
# Debe aparecer: agent model: opencode-go/deepseek-v4-pro
```

---

## 6. Memoria semántica: GitHub Copilot embeddings

OpenClaw usa embeddings para hacer búsqueda semántica en los archivos de memoria del agente (`MEMORY.md`, `memory/*.md`). Sin esto el agente empieza de cero en cada sesión y no puede recuperar contexto de conversaciones anteriores.

### Por qué GitHub Copilot y no otras opciones

| Opción | Ventaja | Desventaja |
|---|---|---|
| `github-copilot` | Sin costo extra (Student Pack), sin descarga | Requiere internet |
| `local` | Offline, sin APIs | Descarga ~600MB, consume CPU del Celeron |
| `gemini` | — | Cuota limitada, puede fallar con key expirada |
| `openai` | Buena calidad | Cuesta dinero |

Para este setup se usa **GitHub Copilot** por estar incluido en el Student Pack.

### Configurar GitHub Copilot en OpenClaw

```bash
sudo su - openclaw_user
openclaw onboard --auth-choice github-copilot
```

El wizard abre el flujo OAuth de GitHub:
1. Te muestra una URL (`https://github.com/login/device`) y un código de 9 caracteres
2. Abres la URL en el navegador, ingresas el código y autorizas con tu cuenta de GitHub
3. **El código expira en 15 minutos** — hacerlo de inmediato
4. Config handling → `Use existing values`
5. Select channel → `Skip for now` (Telegram ya está configurado)

**IMPORTANTE:** el onboarding cambia el modelo primario a `github-copilot/claude-opus-4.7` automáticamente. Hay que restaurarlo después:

```bash
openclaw config set agents.defaults.model.primary "opencode-go/deepseek-v4-pro"
```

### Configurar memory search para usar Copilot

```bash
openclaw config set agents.defaults.memorySearch '{"provider": "github-copilot"}' --strict-json
exit
sudo systemctl restart openclaw
```

### Verificar que funciona

Desde Telegram:
```
¿Qué recuerdas de mí?
```

Si responde sin errores de Gemini o "database is not open", está funcionando. La primera vez devuelve 0 resultados porque la base de datos está vacía — es normal.

### Kickstarter de memoria

Para que el agente tenga contexto base desde el inicio, guardar un perfil manualmente:

```
Guarda esto en memoria: [tu nombre], estudiante de CS último ciclo, usuario de Arch Linux como cliente y Debian Trixie bare-metal como servidor. Corro OpenClaw 2026.5.7 con DeepSeek V4 Pro como modelo primario y Tavily para web search. El servidor es un Celeron con Jellyfin y medios en /srv/.
```

El agente indexa el texto automáticamente y lo recupera en sesiones futuras con `memory_search`.

### Modelo de embeddings resultante

- **Provider:** `github-copilot`
- **Modelo:** `text-embedding-3-small`
- **Backend:** SQLite local (`~/.openclaw/workspace/`)
- **Sin dependencia de Gemini**

---

## 7. Web search: Tavily

OpenClaw soporta múltiples providers de búsqueda web. Para este setup se eligió **Tavily** (diseñado para agentes LLM) sobre DuckDuckGo (experimental, keyless) y Gemini (cuota limitada, puede generar costo).

> **Nota para estudiantes:** Tavily tiene plan gratuito para estudiantes en tavily.com usando correo universitario. El plan free normal incluye 1,000 créditos/mes, suficiente para uso de agente cotidiano.

Configurar vía wizard:

```bash
sudo su - openclaw_user
openclaw configure --section tools
```

Seleccionar Tavily como provider e ingresar la API key. Después habilitar el plugin explícitamente:

```bash
openclaw plugins enable tavily
exit
sudo systemctl restart openclaw
```

Verificar que el agente tiene acceso desde Telegram:
```
¿Tienes acceso a búsqueda web? ¿Qué herramientas tienes disponibles?
```

Debe responder mencionando `web_search` y `web_fetch`.

---

## 8. Migración entre versiones: qué hacer cuando hay breaking changes

Al actualizar de 2026.3.13 a 2026.5.7 hubo varios breaking changes en el schema de `openclaw.json`. El flujo correcto para futuras actualizaciones:

```bash
# 1. Actualizar el paquete
sudo su - openclaw_user
npm install -g openclaw@latest

# 2. Si el CLI falla con "Invalid config", correr el doctor ANTES de reiniciar el gateway
openclaw doctor --fix

# 3. Reiniciar desde el usuario principal
exit
sudo systemctl daemon-reload
sudo systemctl restart openclaw
```

### Breaking changes conocidos (2026.3.13 → 2026.5.7)

- `channels.telegram.streaming` pasó de ser un valor escalar (`"partial"`) a ser un objeto (`{ "mode": "partial" }`). El doctor lo migra automáticamente.
- `tools.web.search.provider: "gemini"` ya no es válido. Usar `"duckduckgo"`, `"tavily"`, u otro provider del listado actual.
- El flag `--merge` en `openclaw config set` puede no estar disponible en todas las versiones; editar el JSON directamente es más confiable.

### Traba: `openclaw models list` se cuelga con systemd de sistema

En 2026.5.7 con el gateway corriendo como servicio de sistema (no de usuario), el CLI de `models list` puede quedarse colgado indefinidamente. Esto es un bug conocido y **no afecta el funcionamiento real del agente**. Workarounds:

- Verificar modelos directamente desde Telegram: `/model opencode-go/deepseek-v4-pro`
- Consultar el modelo activo en los logs: `sudo journalctl -u openclaw -f`
- El agente responde `Model set to X for this session` si el modelo existe en el catálogo

---

## 9. Capacidades del agente con OpenCode Go

El agente entiende su propio stack de modelos y puede orquestarlos. Desde Telegram:

- **Cambiar de modelo en sesión:** `/model opencode-go/deepseek-v4-pro`
- **Por alias:** `/model DeepSeek-Pro`
- **Lanzar subagentes con modelo específico:** "Usa Kimi para revisar este documento largo"
- **Tareas paralelas:** lanzar subagentes simultáneos con modelos distintos

Uso recomendado por modelo:
- **DeepSeek V4 Pro** → modelo primario, coding avanzado, tareas agénticas, investigación extensa — mejor benchmark open-weight general (80.6% SWE-bench)
- **DeepSeek V4 Flash** → tareas rápidas, respuestas cortas, bajo consumo de cuota
- **Kimi K2.6** → documentos muy largos, PDFs, frontend, 256K contexto — usar explícitamente cuando se necesite; **no usar como primario** (bug conocido: thinking mode se activa siempre en subagentes, causa error 400)
- **MiniMax M2.7** → coding general intensivo
- **GLM-5.1** → razonamiento matemático y lógica
- **Qwen3.6 Plus** → coding y razonamiento mixto, buen tool-calling

---

## 10. Permisos para medios de Jellyfin

El servidor también corre **Jellyfin** con medios en `/srv/`. Para que `openclaw_user` pueda operar sobre esas carpetas creé un grupo compartido:

```bash
sudo groupadd media
sudo usermod -aG media [mi-usuario]
sudo usermod -aG media openclaw_user

sudo chown -R root:media /srv/Pelis /srv/Series
sudo chmod -R 775 /srv/Pelis /srv/Series

# Symlinks en el workspace del agente
sudo ln -s /srv/Pelis /home/openclaw_user/Pelis
sudo ln -s /srv/Series /home/openclaw_user/Series

sudo systemctl restart openclaw
```

---

## 11. Cheat sheet de comandos

### Gestión del servicio (usuario principal)

```bash
# Ver logs en tiempo real (fundamental para depurar)
sudo journalctl -u openclaw -f

# Reiniciar (necesario tras cambios en openclaw.json)
sudo systemctl restart openclaw

# Detener el agente
sudo systemctl stop openclaw

# Estado del servicio
sudo systemctl status openclaw
```

### Mantenimiento y updates (como openclaw_user)

```bash
sudo su - openclaw_user

# Actualizar OpenClaw
npm install -g openclaw@latest

# Migrar config tras update (siempre antes de reiniciar)
openclaw doctor --fix

# Chat local por terminal (TUI)
openclaw tui

# Ver estado del gateway
openclaw gateway status

# Ver modelos disponibles por provider (puede colgarse con systemd de sistema — ver sección 7)
openclaw models list --provider opencode-go

# Setear modelo primario
openclaw config set agents.defaults.model.primary "opencode-go/deepseek-v4-pro"

# Ver estado de los canales conectados
openclaw channels status

# Habilitar/deshabilitar plugins
openclaw plugins enable tavily
openclaw plugins disable tavily

# Re-autenticar OpenCode Go si expira
openclaw onboard --auth-choice opencode-go

# Re-autenticar GitHub Copilot si expira (OAuth, abre el navegador)
openclaw onboard --auth-choice github-copilot
# → Config handling: Use existing values
# → Channel: Skip for now
# → Después restaurar modelo primario (el onboarding lo sobreescribe a claude-opus-4.7):
openclaw config set agents.defaults.model.primary "opencode-go/deepseek-v4-pro"

# Aprobar pairing de nuevo usuario en Telegram
openclaw pairing approve telegram [CODIGO]
```

### Desde Telegram

```
# Cambiar modelo en sesión
/model opencode-go/deepseek-v4-pro
/model Kimi-Pro

# Ver modelo actual
/model status

# Listar modelos disponibles
/model list

# Comandos de owner (solo con commands.ownerAllowFrom configurado)
/config
/diagnostics
```

---

## 12. Pendientes

- [ ] Configurar failover en cadena en `openclaw.json`: DeepSeek V4 Pro → MiniMax M2.7 → DeepSeek V4 Flash
- [ ] Skills: instalar `nano-pdf` (requiere `uv`), `session-logs` (requiere `jq` y `ripgrep`), `summarize`
- [ ] Verificar permisos de `/srv/` para `openclaw_user` con el grupo `media`
- [ ] Navidrome: aplicar configuración de Cloudflare Tunnel si se quiere acceso externo (`navidrome.[mi-dominio].app → http://localhost:4533`)
- [x] Hardening SSH en Debian: clave copiada vía tunnel (`ssh-copy-id` con ProxyCommand), acceso sin contraseña verificado desde Arch