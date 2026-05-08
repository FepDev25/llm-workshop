# Cómo desplegué OpenClaw en un servidor Debian bare-metal

**Entorno:** Debian Trixie — bare-metal Celeron
**Versión de OpenClaw:** 2026.3.13
**Modelo de IA:** OpenCode Go (Kimi K2.5 como primario)
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

[Install]
WantedBy=multi-user.target
```

```bash
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

---

## 5. Migración a OpenCode Go (Kimi K2.5)

OpenCode Go es una suscripción de $5 el primer mes y $10/mes que da acceso a modelos open source de calidad optimizados para coding. Con el plan base tienes disponibles:

| Model ref | Modelo | Fortaleza |
|---|---|---|
| `opencode-go/kimi-k2.5` | Kimi K2.5 | Frontend, contexto 256K, multimodal |
| `opencode-go/minimax-m2.5` | MiniMax M2.5 | Mejor coding general (SWE-Bench 80.2%), más requests |
| `opencode-go/glm-5` | GLM-5 | Razonamiento matemático |

### Por qué el `.env` va en `~/.openclaw/.env`

OpenClaw tiene un orden de precedencia estricto para variables de entorno. La ubicación correcta para credenciales en un servicio systemd es `~/.openclaw/.env`, **no** `~/.env`. El `EnvironmentFile` del service debe apuntar ahí.

### Proceso de migración

**1. Actualizar el `EnvironmentFile` en el service** (desde el usuario principal):

```bash
sudo nano /etc/systemd/system/openclaw.service
```

Verificar que la línea diga:
```ini
EnvironmentFile=/home/openclaw_user/.openclaw/.env
```

**2. Correr el onboarding interactivo de OpenCode Go** (como `openclaw_user`):

```bash
sudo su - openclaw_user
openclaw onboard --auth-choice opencode-go
```

El asistente detecta el config existente. Seleccionar:
- Config handling → `Use existing values`
- Web search → `Skip for now`
- Skills → `Skip for now` (se pueden configurar después)

Al terminar el onboarding, la API key queda guardada en el auth store interno de OpenClaw (`~/.local/share/opencode/auth.json`), que es donde el provider `opencode-go` la busca.

**3. Verificar que los modelos tienen auth:**

```bash
openclaw models list --provider opencode-go
```

Debe mostrar `yes` en la columna Auth para los 3 modelos. Si alguno muestra `missing`, el onboarding no completó correctamente.

**4. Setear el modelo primario:**

```bash
openclaw config set agents.defaults.model.primary "opencode-go/kimi-k2.5"
```

**5. Reiniciar el servicio** (desde el usuario principal):

```bash
exit
sudo systemctl daemon-reload
sudo systemctl restart openclaw
```

**6. Verificar en los logs:**

```bash
sudo journalctl -u openclaw -f
```

Debe aparecer la línea:
```
agent model: opencode-go/kimi-k2.5
```

---

## 6. Capacidades del agente con OpenCode Go

El agente entiende su propio stack de modelos y puede orquestarlos. Desde Telegram se puede:

- **Cambiar de modelo en sesión:** "Cámbiate a MiniMax para esto"
- **Lanzar subagentes con modelo específico:** "Usa Kimi para revisar este documento largo"
- **Tareas paralelas:** lanzar subagentes simultáneos con modelos distintos

Uso recomendado por modelo:
- **MiniMax M2.5** → coding general, mejor benchmark, más requests disponibles
- **Kimi K2.5** → documentos largos, PDFs, frontend, contexto 256K
- **GLM-5** → razonamiento matemático y lógica

---

## 7. Permisos para medios de Jellyfin

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

## 8. Cheat sheet de comandos

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

# Ver modelos disponibles por provider
openclaw models list --provider opencode-go

# Setear modelo primario
openclaw config set agents.defaults.model.primary "opencode-go/minimax-m2.5"

# Ver estado de los canales conectados
openclaw channels status

# Re-autenticar OpenCode Go si expira
openclaw onboard --auth-choice opencode-go
```

---

## 9. Pendientes

- [ ] Configurar failover en cadena en `openclaw.json`: MiniMax → Kimi → GLM
- [ ] Explorar skills útiles: `github`, `nano-pdf`, `summarize`
- [ ] Verificar permisos de `/srv/` para `openclaw_user` con el grupo `media`