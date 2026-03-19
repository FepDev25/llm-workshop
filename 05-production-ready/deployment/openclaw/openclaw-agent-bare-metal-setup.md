# Cómo desplegué OpenClaw en un servidor Debian bare-metal

**Entorno:** Debian Trixie — bare-metal Celeron
**Versión de OpenClaw:** 2026.3.13
**Modelo de IA:** Gemini 3.1 Pro (Google Cloud API)
**Interfaz principal:** Telegram

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

# Instalar OpenClaw
npm install -g openclaw@latest
```

### API key de Gemini

```bash
nano ~/.env
```

```env
GEMINI_API_KEY="[tu-api-key]"
```

### Setup inicial (crítico)

Antes de levantar cualquier servicio, hay que correr el asistente de configuración. Esto crea la estructura de carpetas que OpenClaw necesita para funcionar:

```bash
openclaw setup
```

---

## 3. Cambiar el modelo a Gemini 3.1 Pro

Por defecto, OpenClaw viene configurado para usar Claude. Lo cambié editando el archivo de configuración principal:

```bash
nano ~/.openclaw/openclaw.json
```

Modifiqué **únicamente** el bloque `agents`:

```json
"agents": {
  "defaults": {
    "workspace": "/home/openclaw_user/.openclaw/workspace",
    "model": "google/gemini-3.1-pro-preview",
    "compaction": {
      "mode": "safeguard"
    }
  }
},
```

---

## 4. Servicio systemd para que corra 24/7

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
EnvironmentFile=/home/openclaw_user/.env
# IMPORTANTE: en versiones recientes usar 'gateway --force', no 'start' ni 'daemon'
ExecStart=/home/openclaw_user/.npm-global/bin/openclaw gateway --force
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw
```

---

## 5. Conectar Telegram como interfaz de chat

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

Y listo — el bot empezó a responder.

---

## 6. Cheat sheet de comandos

### Gestión del servicio (usuario principal)

```bash
# Ver logs en tiempo real (fundamental para depurar)
sudo journalctl -u openclaw -f

# Reiniciar (necesario tras cambios en openclaw.json)
sudo systemctl restart openclaw

# Detener el agente
sudo systemctl stop openclaw
```

### Interacción local (como openclaw_user)

```bash
sudo su - openclaw_user

# Chat local por terminal (TUI)
openclaw tui

# Ver estado de los canales conectados
openclaw channels status
```

---

## 7. Para qué lo uso

- Redactando...
