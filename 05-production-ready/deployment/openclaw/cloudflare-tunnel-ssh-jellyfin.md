# Acceso remoto a mi servidor Debian sin abrir puertos: SSH + Jellyfin vía Cloudflare Tunnel

**Fecha:** Marzo 2026
**Entorno:** Arch Linux (cliente) → Debian Trixie (servidor, bare-metal Celeron)
**Dominio:** `[mi-dominio].app` (obtenido gratis con GitHub Student Pack)
**Resultado:** SSH y Jellyfin accesibles desde cualquier red del mundo, sin tocar el router.

---

Tengo un servidor bare-metal en casa corriendo Debian Trixie. El problema clásico: quería acceder a él desde cualquier lugar, pero mi router no tiene IP pública fija y no quería abrir puertos (ni lidiar con el NAT del ISP). La solución que encontré fue usar **Cloudflare Tunnel**, y funcionó perfectamente.

---

## La arquitectura que armé

```
Mi Arch Linux (desde cualquier red)
        │
        ▼
Cloudflare Edge (cifrado TLS)
        │
        ▼
cloudflared daemon en Debian (conexión saliente, sin puertos abiertos)
        ├── ssh://localhost:22   →   ssh.[mi-dominio].app
        └── http://localhost:8096 →  jellyfin.[mi-dominio].app
```

Lo que me gustó de esta arquitectura:
- Sin port forwarding en el router
- Sin IP pública fija necesaria
- Todo el tráfico cifrado por Cloudflare
- El servidor nunca acepta conexiones entrantes directas

---

## 1. SSH en Debian

Primero lo básico: levantar el servidor SSH y configurar acceso con clave.

```bash
sudo apt update
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
```

Para verificar la IP local del servidor:

```bash
ip a
# Buscar la interfaz (eth0, enp3s0, etc.) → anotar la IP, ej: 192.168.1.x
```

### Clave SSH (sin contraseña)

```bash
# En Arch: generar clave si no existe
ssh-keygen -t ed25519 -C "arch-to-debian"

# Copiar clave pública al servidor
ssh-copy-id [mi-usuario]@192.168.1.x
```

Alias que agregué a `~/.zshrc` para conexión en red local:

```bash
alias debian-local='ssh [mi-usuario]@192.168.1.x'
```

---

## 2. Instalar cloudflared en Debian (con un problema inesperado)

Acá me encontré con el primer obstáculo: **el repositorio `apt` oficial de Cloudflare da 404 en Debian Trixie**. Cloudflare no tiene soporte apt para Debian 13 todavía.

```
Err:8 https://pkg.cloudflare.com trixie Release
  404  Not Found
```

**Solución:** descargar el `.deb` directamente desde GitHub Releases. Este comando detecta la arquitectura automáticamente:

```bash
curl --location --output cloudflared.deb \
  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$(dpkg --print-architecture).deb" \
  && sudo dpkg -i cloudflared.deb

cloudflared --version
# cloudflared version 2026.3.0
```

Resulta que esta es además la forma que recomienda la documentación oficial de Cloudflare para instalaciones manuales.

---

## 3. Configurar el Cloudflare Tunnel

### Paso 1: crear el tunnel en el dashboard

Fui a la consola de Cloudflare Zero Trust → **Networks → Tunnels → Create a tunnel**, elegí Cloudflared como conector y le puse de nombre `debian-server`. El dashboard me generó un comando con un token (`eyJ...`).

### Paso 2: instalar el servicio en Debian

```bash
sudo cloudflared service install [TOKEN-DEL-DASHBOARD]

sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
# Debe aparecer "Active: active (running)"
```

### Paso 3: configurar las rutas públicas

En el dashboard: **tunnel debian-server → Routes → Add route → Published application**

| Hostname | Service URL | Descripción |
|---|---|---|
| `ssh.[mi-dominio].app` | `ssh://localhost:22` | Acceso SSH al servidor |
| `jellyfin.[mi-dominio].app` | `http://localhost:8096` | Interfaz web de Jellyfin |

**Traba que tuve acá:** el campo Service URL requiere protocolo explícito. Si le pones `localhost:22` sin el `ssh://` adelante, el dashboard tira error.

El DNS se configura automáticamente al crear cada ruta — Cloudflare se encarga de todo.

---

## 4. El dominio: gratis con GitHub Student Pack

El dominio lo conseguí gratis gracias al Student Pack de GitHub. Las opciones que vi disponibles:

| Proveedor | Oferta |
|---|---|
| **Name.com** | Dominio gratis con extensiones `.live`, `.studio`, `.app`, `.dev` y 25+ más |
| **Namecheap** | 1 año gratis del TLD `.me` + 1 SSL gratis |

Fui por Name.com y registré mi dominio.

### Apuntar el dominio a Cloudflare

1. En Cloudflare: **Add a site** → mi dominio → plan **Free**
2. Cloudflare escanea el DNS y me dio dos nameservers propios
3. En Name.com: **Manage Nameservers** → reemplacé los nameservers por los de Cloudflare
4. Esperé unos 10 minutos para que propagara
5. El dominio apareció como **Active** en el dashboard de Cloudflare

---

## 5. Configurar el cliente SSH en Arch

```bash
sudo pacman -S cloudflared
```

Agregué esto a `~/.ssh/config`:

```
Host ssh.[mi-dominio].app
    User [mi-usuario]
    ProxyCommand cloudflared access ssh --hostname %h
    IdentityFile ~/.ssh/id_ed25519
```

Con eso, conectarme desde cualquier red del mundo es simplemente:

```bash
ssh ssh.[mi-dominio].app
```

La primera vez abre el navegador para autenticarme con mi cuenta de Cloudflare. Después queda en caché.

Para copiar la clave SSH a través del tunnel (evitar contraseña):

```bash
ssh-copy-id -o ProxyCommand="cloudflared access ssh --hostname ssh.[mi-dominio].app" [mi-usuario]@ssh.[mi-dominio].app
```

---

## 6. Jellyfin: acceso web directo

Con las rutas del tunnel configuradas, Jellyfin quedó accesible desde el navegador sin configuración adicional en el cliente. Cloudflare maneja el SSL automáticamente (HTTPS gratis).

---

## 7. Permisos para OpenClaw

El servidor también corre **OpenClaw** bajo un usuario restringido sin sudo (`openclaw_user`). Para darle acceso a las carpetas de medios de Jellyfin en `/srv/` creé un grupo compartido:

```bash
sudo groupadd media
sudo usermod -aG media [mi-usuario]
sudo usermod -aG media openclaw_user

sudo chown -R root:media /srv/Pelis /srv/Series
sudo chmod -R 775 /srv/Pelis /srv/Series

# Symlinks en el workspace del agente para que pueda operar sobre los medios
sudo ln -s /srv/Pelis /home/openclaw_user/Pelis
sudo ln -s /srv/Series /home/openclaw_user/Series

sudo systemctl restart openclaw
```

---

## 8. Cheat sheet de comandos

### En Debian (servidor)

```bash
# Estado y logs del tunnel
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -f

# Reiniciar el tunnel
sudo systemctl restart cloudflared

# Estado de SSH e IP local
sudo systemctl status ssh
ip a

# Versión de cloudflared
cloudflared --version
```

### En Arch (cliente)

```bash
# Conectarse al servidor
ssh ssh.[mi-dominio].app

# Copiar clave SSH a través del tunnel
ssh-copy-id -o ProxyCommand="cloudflared access ssh --hostname ssh.[mi-dominio].app" [mi-usuario]@ssh.[mi-dominio].app

# Cerrar sesión de cloudflared (si hay que reautenticarse)
cloudflared access logout ssh.[mi-dominio].app

# Conexión con verbose (para debug)
ssh -v ssh.[mi-dominio].app
```

---

## 9. Pendientes

- [ ] Hardening SSH en Debian: desactivar `PasswordAuthentication` ahora que la clave está copiada
- [ ] Verificar permisos de `/srv/` para `openclaw_user` con el grupo `media`
- [ ] Navidrome: aplicar la misma configuración si quiero acceso externo (`navidrome.[mi-dominio].app → http://localhost:4533`)
