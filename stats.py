"""
Veracious Dashboard — Stats Collector
Runs as a background service and exposes a JSON API on port 8889.
Edit config.py to enable/disable integrations.
"""

import json
import time
import threading
import requests
import urllib3

from flask import Flask, request
import config as cfg

# Suppress SSL warnings for self-signed certs (common on local network devices)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ─── Cache ────────────────────────────────────────────────────────────────────
# Fast cache: network speeds, updated every CACHE_SECONDS
# Slow cache: everything else, updated every SLOW_CACHE_SECONDS

_fast_cache  = {'data': {}, 'time': 0}
_slow_cache  = {'data': {}, 'time': 0}
_cache_lock  = threading.Lock()

# ─── MikroTik ─────────────────────────────────────────────────────────────────

_mikrotik_prev = {'tx': 0, 'rx': 0, 'time': 0}

def get_mikrotik_stats():
    if not cfg.MIKROTIK_ENABLED:
        return {}
    try:
        import routeros_api
        connection = routeros_api.RouterOsApiPool(
            cfg.MIKROTIK_HOST,
            username=cfg.MIKROTIK_USER,
            password=cfg.MIKROTIK_PASS,
            port=cfg.MIKROTIK_PORT,
            plaintext_login=True
        )
        api = connection.get_api()

        ifaces = api.get_resource('/interface')
        wan = None
        for iface in ifaces.get():
            if iface.get('name') == cfg.MIKROTIK_WAN_IF:
                wan = iface
                break

        leases = api.get_resource('/ip/dhcp-server/lease')
        active_leases = [l for l in leases.get() if l.get('status') == 'bound']
        connection.disconnect()

        now = time.time()
        tx_bytes = int(wan.get('tx-byte', 0)) if wan else 0
        rx_bytes = int(wan.get('rx-byte', 0)) if wan else 0

        tx_speed = rx_speed = 0.0
        elapsed = now - _mikrotik_prev['time']
        if _mikrotik_prev['time'] > 0 and elapsed > 0:
            tx_speed = (tx_bytes - _mikrotik_prev['tx']) / elapsed / 1024 / 1024
            rx_speed = (rx_bytes - _mikrotik_prev['rx']) / elapsed / 1024 / 1024

        _mikrotik_prev['tx'] = tx_bytes
        _mikrotik_prev['rx'] = rx_bytes
        _mikrotik_prev['time'] = now

        return {
            'mikrotik_up_mbps':       round(max(tx_speed, 0), 2),
            'mikrotik_down_mbps':     round(max(rx_speed, 0), 2),
            'mikrotik_devices':       len(active_leases),
        }
    except Exception as e:
        return {'mikrotik_error': str(e)}


# ─── Pi-hole v6 ───────────────────────────────────────────────────────────────
# Persistent session: authenticate once, reuse the token, only re-auth if it
# is rejected (401) or has expired. This avoids burning through API seats.

_pihole_sid        = None
_pihole_sid_expiry = 0   # Unix timestamp after which we must re-auth

def _pihole_authenticate():
    """Login and cache the session ID + its validity window."""
    global _pihole_sid, _pihole_sid_expiry
    auth = requests.post(
        f'{cfg.PIHOLE_HOST}/api/auth',
        json={'password': cfg.PIHOLE_PASS},
        timeout=5
    )
    auth.raise_for_status()
    body    = auth.json()
    session = body.get('session', {})
    sid     = session.get('sid')
    if not sid:
        raise RuntimeError(f'Pi-hole auth failed: {body}')
    # Pi-hole v6 sessions last 5 minutes by default; refresh at 4 min to be safe
    validity = session.get('validity', 300)
    _pihole_sid        = sid
    _pihole_sid_expiry = time.time() + min(validity, 240)
    return sid

def get_pihole_stats():
    if not cfg.PIHOLE_ENABLED:
        return {}
    global _pihole_sid, _pihole_sid_expiry
    try:
        # Re-auth only if token is missing or about to expire
        if not _pihole_sid or time.time() >= _pihole_sid_expiry:
            _pihole_authenticate()

        res = requests.get(
            f'{cfg.PIHOLE_HOST}/api/stats/summary',
            headers={'sid': _pihole_sid},
            timeout=5
        )

        # Token was rejected mid-cycle — re-auth once and retry
        if res.status_code == 401:
            _pihole_authenticate()
            res = requests.get(
                f'{cfg.PIHOLE_HOST}/api/stats/summary',
                headers={'sid': _pihole_sid},
                timeout=5
            )

        res.raise_for_status()
        data = res.json()

        return {
            'pihole_blocked': data['queries']['blocked'],
            'pihole_percent': round(data['queries']['percent_blocked'], 1),
            'pihole_total':   data['queries']['total'],
            'pihole_gravity': data['gravity']['domains_being_blocked'],
        }
    except Exception as e:
        # Invalidate cached session so next poll tries a fresh login
        _pihole_sid        = None
        _pihole_sid_expiry = 0
        return {'pihole_error': str(e)}

# ─── Proxmox ──────────────────────────────────────────────────────────────────

def get_proxmox_stats():
    if not cfg.PROXMOX_ENABLED:
        return {}
    try:
        headers = {
            'Authorization': f'PVEAPIToken={cfg.PROXMOX_USER}!{cfg.PROXMOX_TOKEN_ID}={cfg.PROXMOX_TOKEN}'
        }
        res = requests.get(
            f'{cfg.PROXMOX_HOST}/api2/json/nodes/{cfg.PROXMOX_NODE}/status',
            headers=headers,
            verify=cfg.PROXMOX_VERIFY_SSL,
            timeout=5
        )
        data = res.json()['data']

        vms = requests.get(
            f'{cfg.PROXMOX_HOST}/api2/json/nodes/{cfg.PROXMOX_NODE}/qemu',
            headers=headers,
            verify=cfg.PROXMOX_VERIFY_SSL,
            timeout=5
        ).json()['data']

        running_vms = len([v for v in vms if v.get('status') == 'running'])

        return {
            'proxmox_cpu_pct':    round(data['cpu'] * 100, 1),
            'proxmox_mem_pct':    round(data['memory']['used'] / data['memory']['total'] * 100, 1),
            'proxmox_vms':        running_vms,
        }
    except Exception as e:
        return {'proxmox_error': str(e)}


# ─── TrueNAS ──────────────────────────────────────────────────────────────────

def get_truenas_stats():
    if not cfg.TRUENAS_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.TRUENAS_API_KEY}'}
        res = requests.get(
            f'{cfg.TRUENAS_HOST}/api/v2.0/pool',
            headers=headers,
            timeout=5
        )
        pools = res.json()
        healthy = all(p.get('healthy') for p in pools)

        disk_res = requests.get(
            f'{cfg.TRUENAS_HOST}/api/v2.0/disk',
            headers=headers,
            timeout=5
        )
        disk_count = len(disk_res.json())

        return {
            'truenas_pools':    len(pools),
            'truenas_healthy':  'Yes' if healthy else 'No',
            'truenas_disks':    disk_count,
        }
    except Exception as e:
        return {'truenas_error': str(e)}


# ─── UniFi ────────────────────────────────────────────────────────────────────

def get_unifi_stats():
    if not cfg.UNIFI_ENABLED:
        return {}
    try:
        session = requests.Session()
        session.verify = cfg.UNIFI_VERIFY_SSL
        session.post(
            f'{cfg.UNIFI_HOST}/api/login',
            json={'username': cfg.UNIFI_USER, 'password': cfg.UNIFI_PASS},
            timeout=5
        )
        res = session.get(
            f'{cfg.UNIFI_HOST}/api/s/{cfg.UNIFI_SITE}/stat/sta',
            timeout=5
        )
        clients = res.json().get('data', [])
        session.post(f'{cfg.UNIFI_HOST}/api/logout')

        return {
            'unifi_clients': len(clients),
        }
    except Exception as e:
        return {'unifi_error': str(e)}


# ─── Plex ─────────────────────────────────────────────────────────────────────

def get_plex_stats():
    if not cfg.PLEX_ENABLED:
        return {}
    try:
        res = requests.get(
            f'{cfg.PLEX_HOST}/status/sessions',
            headers={'X-Plex-Token': cfg.PLEX_TOKEN, 'Accept': 'application/json'},
            timeout=5
        )
        data = res.json()
        streams = data.get('MediaContainer', {}).get('size', 0)

        return {
            'plex_streams': streams,
        }
    except Exception as e:
        return {'plex_error': str(e)}


# ─── Home Assistant ───────────────────────────────────────────────────────────

def get_ha_stats():
    if not cfg.HA_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.HA_TOKEN}'}
        res = requests.get(
            f'{cfg.HA_HOST}/api/',
            headers=headers,
            timeout=5
        )
        states = requests.get(
            f'{cfg.HA_HOST}/api/states',
            headers=headers,
            timeout=5
        ).json()

        entity_count = len(states)
        automations = len([s for s in states if s['entity_id'].startswith('automation.')])

        return {
            'ha_entities':     entity_count,
            'ha_automations':  automations,
        }
    except Exception as e:
        return {'ha_error': str(e)}


# ─── Portainer ────────────────────────────────────────────────────────────────

def get_portainer_stats():
    if not cfg.PORTAINER_ENABLED:
        return {}
    try:
        headers = {'X-API-Key': cfg.PORTAINER_TOKEN}
        containers = requests.get(
            f'{cfg.PORTAINER_HOST}/api/endpoints/1/docker/containers/json?all=true',
            headers=headers,
            timeout=5
        ).json()

        running = len([c for c in containers if c.get('State') == 'running'])
        total   = len(containers)

        return {
            'portainer_running':  running,
            'portainer_total':    total,
        }
    except Exception as e:
        return {'portainer_error': str(e)}


# ─── Ollama ───────────────────────────────────────────────────────────────────

def get_ollama_stats():
    if not cfg.OLLAMA_ENABLED:
        return {}
    try:
        res = requests.get(f'{cfg.OLLAMA_HOST}/api/tags', timeout=5)
        models = res.json().get('models', [])
        return {
            'ollama_models': len(models),
        }
    except Exception as e:
        return {'ollama_error': str(e)}


# ─── Open WebUI ───────────────────────────────────────────────────────────────

def get_openwebui_stats():
    if not cfg.OPENWEBUI_ENABLED:
        return {}
    try:
        headers = {}
        if hasattr(cfg, 'OPENWEBUI_TOKEN') and cfg.OPENWEBUI_TOKEN:
            headers['Authorization'] = f'Bearer {cfg.OPENWEBUI_TOKEN}'
        res = requests.get(
            f'{cfg.OPENWEBUI_HOST}/api/models',
            headers=headers,
            timeout=5
        )
        models = res.json().get('data', [])
        return {
            'openwebui_models': len(models),
        }
    except Exception as e:
        return {'openwebui_error': str(e)}


# ─── Grafana ──────────────────────────────────────────────────────────────────

def get_grafana_stats():
    if not cfg.GRAFANA_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.GRAFANA_TOKEN}'}
        dashboards = requests.get(
            f'{cfg.GRAFANA_HOST}/api/search?type=dash-db',
            headers=headers,
            timeout=5
        ).json()
        return {
            'grafana_dashboards': len(dashboards),
        }
    except Exception as e:
        return {'grafana_error': str(e)}


# ─── BlueBubbles ─────────────────────────────────────────────────────────────
# BlueBubbles is a macOS iMessage relay server. Auth uses ?password= query param.
# Exposes /api/v1/server/info and /api/v1/chat/query for useful dashboard stats.

def get_bluebubbles_stats():
    if not getattr(cfg, 'BLUEBUBBLES_ENABLED', False):
        return {}
    try:
        base     = cfg.BLUEBUBBLES_HOST.rstrip('/')
        password = cfg.BLUEBUBBLES_PASS
        params   = {'password': password}

        # Server info — uptime, Private API status, connected devices
        info_res = requests.get(
            f'{base}/api/v1/server/info',
            params=params,
            timeout=5
        )
        info_res.raise_for_status()
        info = info_res.json().get('data', {})

        private_api = info.get('is_using_private_api', False)
        imessage_connected = info.get('detected_icloud', False)

        # Total chat count
        chat_res = requests.post(
            f'{base}/api/v1/chat/query',
            params=params,
            json={'limit': 1, 'offset': 0},
            timeout=5
        )
        chat_res.raise_for_status()
        chat_data  = chat_res.json()
        chat_count = chat_data.get('metadata', {}).get('total', 0)

        # Message count for today (messages in last 24h)
        import time as _time
        since_ms = int((_time.time() - 86400) * 1000)
        msg_res = requests.post(
            f'{base}/api/v1/message/query',
            params=params,
            json={'limit': 1, 'offset': 0, 'after': since_ms},
            timeout=5
        )
        msg_24h = 0
        if msg_res.ok:
            msg_24h = msg_res.json().get('metadata', {}).get('total', 0)

        return {
            'bluebubbles_chats':        chat_count,
            'bluebubbles_msgs_24h':     msg_24h,
            'bluebubbles_private_api':  'Yes' if private_api else 'No',
            'bluebubbles_imessage':     'Yes' if imessage_connected else 'No',
        }
    except Exception as e:
        return {'bluebubbles_error': str(e)}


# ─── Immich ───────────────────────────────────────────────────────────────────
# Self-hosted Google Photos alternative. Auth via x-api-key header.
# Uses the modern /api/server/statistics endpoint (v1.118+).
# API key needs the server.statistics permission (or admin key).

def get_immich_stats():
    if not getattr(cfg, 'IMMICH_ENABLED', False):
        return {}
    try:
        headers = {
            'x-api-key': cfg.IMMICH_API_KEY,
            'Accept':    'application/json',
        }
        base = cfg.IMMICH_HOST.rstrip('/')

        # Server-wide statistics (photos, videos, usage)
        stats_res = requests.get(
            f'{base}/api/server/statistics',
            headers=headers,
            timeout=5
        )
        stats_res.raise_for_status()
        stats = stats_res.json()

        photos = stats.get('photos', 0)
        videos = stats.get('videos', 0)
        usage_bytes = stats.get('usage', 0)
        # Convert bytes to GB, rounded to 1 decimal
        usage_gb = round(usage_bytes / (1024 ** 3), 1) if usage_bytes else 0

        return {
            'immich_photos': photos,
            'immich_videos': videos,
            'immich_usage_gb': usage_gb,
            'immich_total_assets': photos + videos,
        }
    except Exception as e:
        return {'immich_error': str(e)}


# ─── AMP (CubeCoders) ────────────────────────────────────────────────────────

def get_amp_stats():
    if not getattr(cfg, 'AMP_ENABLED', False):
        return {}
    try:
        base = cfg.AMP_HOST.rstrip('/')

        # Authenticate — returns a sessionToken valid for the request lifetime
        auth_res = requests.post(
            f'{base}/API/Core/Login',
            json={
                'username':       cfg.AMP_USER,
                'password':       cfg.AMP_PASS,
                'token':          '',
                'rememberMeToken': '',
            },
            timeout=8
        )
        auth_res.raise_for_status()
        auth_data = auth_res.json()
        session_id = auth_data.get('sessionID') or auth_data.get('SessionID', '')
        if not session_id:
            return {'amp_error': 'no sessionID in AMP login response'}

        headers = {'Content-Type': 'application/json'}
        payload_base = {'SESSIONID': session_id}

        # Discover all instances
        inst_res = requests.post(
            f'{base}/API/ADSModule/GetInstances',
            json=payload_base,
            headers=headers,
            timeout=8
        )
        inst_res.raise_for_status()
        all_instances = []
        for controller in inst_res.json():
            all_instances.extend(controller.get('AvailableInstances', []))

        filter_ids = getattr(cfg, 'AMP_INSTANCES', [])
        if filter_ids:
            all_instances = [i for i in all_instances if i.get('InstanceID') in filter_ids]

        running      = 0
        total_players = 0
        total_cpu    = 0.0
        total_ram    = 0.0
        counted      = 0

        for inst in all_instances:
            if inst.get('Running'):
                running += 1
            # Pull per-instance status for player counts + resource usage
            try:
                status_res = requests.post(
                    f'{base}/API/ADSModule/GetInstanceStatus',
                    json={**payload_base, 'InstanceId': inst.get('InstanceID', '')},
                    headers=headers,
                    timeout=5
                )
                if status_res.ok:
                    s = status_res.json()
                    metrics = s.get('Metrics', {})
                    players = metrics.get('Active Users', {})
                    total_players += int(players.get('RawValue', 0))
                    cpu = metrics.get('CPU Usage', {})
                    ram = metrics.get('Memory Usage', {})
                    total_cpu += float(cpu.get('Percent', 0))
                    total_ram += float(ram.get('Percent', 0))
                    counted += 1
            except Exception:
                pass

        return {
            'amp_instances_total':   len(all_instances),
            'amp_instances_running': running,
            'amp_players':           total_players,
            'amp_cpu_pct':           round(total_cpu / counted, 1) if counted else 0,
            'amp_ram_pct':           round(total_ram / counted, 1) if counted else 0,
        }
    except Exception as e:
        return {'amp_error': str(e)}


# ─── OctoPrint ────────────────────────────────────────────────────────────────

def _octoprint_printer_stats(printer):
    """Fetch stats for a single OctoPrint instance."""
    host = printer['host'].rstrip('/')
    key  = printer['key']
    headers = {'X-Api-Key': key}

    job_res   = requests.get(f'{host}/api/job',     headers=headers, timeout=5)
    temp_res  = requests.get(f'{host}/api/printer', headers=headers, timeout=5)

    job_res.raise_for_status()
    job  = job_res.json()
    prog = job.get('progress', {})
    state = job.get('state', 'Unknown')
    pct   = round(prog.get('completion') or 0, 1)

    bed_actual = tool_actual = None
    if temp_res.ok:
        temps = temp_res.json().get('temperature', {})
        bed_actual  = temps.get('bed',  {}).get('actual')
        tool_actual = temps.get('tool0', {}).get('actual')

    name = printer.get('name', host)
    prefix = f"octoprint_{name.lower().replace(' ', '_')}"
    result = {
        f'{prefix}_state':    state,
        f'{prefix}_progress': pct,
    }
    if bed_actual  is not None: result[f'{prefix}_bed_temp']     = round(bed_actual,  1)
    if tool_actual is not None: result[f'{prefix}_hotend_temp']  = round(tool_actual, 1)
    return result


def get_octoprint_stats():
    if not getattr(cfg, 'OCTOPRINT_ENABLED', False):
        return {}
    printers = getattr(cfg, 'OCTOPRINT_PRINTERS', [])
    out = {}
    printing_count = 0
    for p in printers:
        try:
            stats = _octoprint_printer_stats(p)
            out.update(stats)
            name   = p.get('name', p['host'])
            prefix = f"octoprint_{name.lower().replace(' ', '_')}"
            if 'Printing' in str(stats.get(f'{prefix}_state', '')):
                printing_count += 1
        except Exception as e:
            name   = p.get('name', p.get('host', 'unknown'))
            prefix = f"octoprint_{name.lower().replace(' ', '_')}"
            out[f'{prefix}_error'] = str(e)
    out['octoprint_printing'] = printing_count
    out['octoprint_total']    = len(printers)
    return out


# ─── Moonraker / Klipper ─────────────────────────────────────────────────────

def _moonraker_printer_stats(printer):
    """Fetch stats for a single Moonraker instance."""
    host = printer['host'].rstrip('/')
    headers = {}
    if printer.get('key'):
        headers['X-Api-Key'] = printer['key']

    # Print stats + temperatures in one call via the objects query endpoint
    objects = 'print_stats,display_status,extruder,heater_bed'
    res = requests.get(
        f'{host}/printer/objects/query?{objects}',
        headers=headers,
        timeout=5
    )
    res.raise_for_status()
    obj = res.json().get('result', {}).get('status', {})

    ps    = obj.get('print_stats', {})
    ds    = obj.get('display_status', {})
    ext   = obj.get('extruder', {})
    bed   = obj.get('heater_bed', {})

    state = ps.get('state', 'unknown')
    pct   = round((ds.get('progress') or 0) * 100, 1)
    ext_t = ext.get('temperature')
    bed_t = bed.get('temperature')

    name   = printer.get('name', host)
    prefix = f"moonraker_{name.lower().replace(' ', '_')}"
    result = {
        f'{prefix}_state':    state,
        f'{prefix}_progress': pct,
    }
    if ext_t is not None: result[f'{prefix}_extruder_temp'] = round(ext_t, 1)
    if bed_t is not None: result[f'{prefix}_bed_temp']      = round(bed_t, 1)
    return result


def get_moonraker_stats():
    if not getattr(cfg, 'MOONRAKER_ENABLED', False):
        return {}
    printers = getattr(cfg, 'MOONRAKER_PRINTERS', [])
    out = {}
    printing_count = 0
    for p in printers:
        try:
            stats = _moonraker_printer_stats(p)
            out.update(stats)
            name   = p.get('name', p['host'])
            prefix = f"moonraker_{name.lower().replace(' ', '_')}"
            if str(stats.get(f'{prefix}_state', '')).lower() == 'printing':
                printing_count += 1
        except Exception as e:
            name   = p.get('name', p.get('host', 'unknown'))
            prefix = f"moonraker_{name.lower().replace(' ', '_')}"
            out[f'{prefix}_error'] = str(e)
    out['moonraker_printing'] = printing_count
    out['moonraker_total']    = len(printers)
    return out


# ─── Bambu Lab (LAN MQTT) ─────────────────────────────────────────────────────
# Uses paho-mqtt to subscribe to the printer's local MQTT topic for ~3 seconds
# and reads the most recent status report.  No cloud account required.

def _bambu_printer_stats(printer):
    """Fetch a single Bambu printer's status via local MQTT."""
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        return {'bambu_error': 'paho-mqtt not installed — run: pip install paho-mqtt --break-system-packages'}

    host        = printer['host']
    serial      = printer['serial']
    access_code = printer['access_code']
    port        = printer.get('port', 1883)
    name        = printer.get('name', serial)
    prefix      = f"bambu_{name.lower().replace(' ', '_')}"

    topic  = f'device/{serial}/report'
    result = {}
    event  = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(topic)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print_data = payload.get('print', {})
            if not print_data:
                return
            state    = print_data.get('gcode_state', 'unknown')
            pct      = print_data.get('mc_percent', 0)
            layer    = print_data.get('layer_num', None)
            total_l  = print_data.get('total_layer_num', None)
            result[f'{prefix}_state']    = state
            result[f'{prefix}_progress'] = pct
            if layer    is not None: result[f'{prefix}_layer']        = layer
            if total_l  is not None: result[f'{prefix}_total_layers'] = total_l
            event.set()
        except Exception:
            pass

    client = mqtt.Client()
    client.username_pw_set('bblp', access_code)
    client.on_connect = on_connect
    client.on_message = on_message

    # Bambu uses TLS on port 8883; LAN mode uses plain 1883
    client.connect(host, port, keepalive=10)
    client.loop_start()
    event.wait(timeout=6)
    client.loop_stop()
    client.disconnect()

    if not result:
        result[f'{prefix}_state'] = 'no_data'
    return result


def get_bambu_stats():
    if not getattr(cfg, 'BAMBU_ENABLED', False):
        return {}
    printers = getattr(cfg, 'BAMBU_PRINTERS', [])
    out = {}
    printing_count = 0
    for p in printers:
        try:
            stats = _bambu_printer_stats(p)
            out.update(stats)
            name   = p.get('name', p.get('serial', 'unknown'))
            prefix = f"bambu_{name.lower().replace(' ', '_')}"
            state  = str(stats.get(f'{prefix}_state', '')).lower()
            if state in ('running', 'printing', 'prepare'):
                printing_count += 1
        except Exception as e:
            name   = p.get('name', p.get('serial', 'unknown'))
            prefix = f"bambu_{name.lower().replace(' ', '_')}"
            out[f'{prefix}_error'] = str(e)
    out['bambu_printing'] = printing_count
    out['bambu_total']    = len(printers)
    return out


# ─── Obico (The Spaghetti Detective) ─────────────────────────────────────────

def get_obico_stats():
    if not getattr(cfg, 'OBICO_ENABLED', False):
        return {}
    try:
        headers = {'Authorization': f'Token {cfg.OBICO_API_KEY}'}
        host    = cfg.OBICO_HOST.rstrip('/')

        res = requests.get(
            f'{host}/api/v1/printer/',
            headers=headers,
            timeout=8
        )
        res.raise_for_status()
        printers = res.json()

        total   = len(printers)
        active  = 0
        out = {'obico_total': total}

        for p in printers:
            name   = p.get('name', f"printer_{p.get('id', '?')}")
            prefix = f"obico_{name.lower().replace(' ', '_')}"
            status = (p.get('print', {}) or {})
            state  = (p.get('status', {}) or {}).get('state', {})
            state_text = state.get('text', 'Unknown') if isinstance(state, dict) else str(state)
            pct    = (p.get('print', {}) or {}).get('progress', 0) or 0

            out[f'{prefix}_state']    = state_text
            out[f'{prefix}_progress'] = round(float(pct), 1)

            if state_text.lower() in ('printing', 'paused'):
                active += 1

        out['obico_active'] = active
        return out
    except Exception as e:
        return {'obico_error': str(e)}


# ─── Cache updater threads ────────────────────────────────────────────────────

def update_fast_cache():
    """Updates frequently-changing stats (network speeds). Runs every CACHE_SECONDS."""
    while True:
        data = {}
        data.update(get_mikrotik_stats())
        with _cache_lock:
            _fast_cache['data'] = data
            _fast_cache['time'] = time.time()
        time.sleep(cfg.CACHE_SECONDS)


def update_slow_cache():
    """Updates slowly-changing stats. Runs every SLOW_CACHE_SECONDS."""
    while True:
        data = {}
        data.update(get_pihole_stats())
        data.update(get_proxmox_stats())
        data.update(get_truenas_stats())
        data.update(get_unifi_stats())
        data.update(get_plex_stats())
        data.update(get_ha_stats())
        data.update(get_portainer_stats())
        data.update(get_ollama_stats())
        data.update(get_openwebui_stats())
        data.update(get_grafana_stats())
        # Media & messaging
        data.update(get_bluebubbles_stats())
        data.update(get_immich_stats())
        # Game servers
        data.update(get_amp_stats())
        # 3D printers
        data.update(get_octoprint_stats())
        data.update(get_moonraker_stats())
        data.update(get_bambu_stats())
        data.update(get_obico_stats())
        with _cache_lock:
            _slow_cache['data'] = data
            _slow_cache['time'] = time.time()
        time.sleep(cfg.SLOW_CACHE_SECONDS)


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route('/stats/fast')
def fast_stats():
    with _cache_lock:
        data = dict(_fast_cache['data'])
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/stats/slow')
def slow_stats():
    with _cache_lock:
        data = dict(_slow_cache['data'])
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/stats')
def all_stats():
    with _cache_lock:
        data = {**_slow_cache['data'], **_fast_cache['data']}
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/health')
def health():
    return app.response_class(
        response=json.dumps({'status': 'ok'}),
        status=200,
        mimetype='application/json'
    )


# ─── Home Assistant Proxy ─────────────────────────────────────────────────────
# Proxies HA API calls from the browser through the backend to avoid CORS.

@app.route('/ha/states')
def ha_states():
    try:
        res = requests.get(
            f'{cfg.HA_HOST}/api/states',
            headers={'Authorization': f'Bearer {cfg.HA_TOKEN}'},
            timeout=8
        )
        response = app.response_class(
            response=res.text,
            status=res.status_code,
            mimetype='application/json'
        )
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return app.response_class(
            response=json.dumps({'error': str(e)}),
            status=500,
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )


@app.route('/ha/toggle', methods=['POST', 'OPTIONS'])
def ha_toggle():
    if request.method == 'OPTIONS':
        r = app.response_class(status=204)
        r.headers['Access-Control-Allow-Origin']  = '*'
        r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return r
    try:
        body      = request.get_json()
        entity_id = body.get('entity_id', '')
        res = requests.post(
            f'{cfg.HA_HOST}/api/services/homeassistant/toggle',
            headers={
                'Authorization': f'Bearer {cfg.HA_TOKEN}',
                'Content-Type':  'application/json',
            },
            json={'entity_id': entity_id},
            timeout=8
        )
        response = app.response_class(
            response=res.text,
            status=res.status_code,
            mimetype='application/json'
        )
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return app.response_class(
            response=json.dumps({'error': str(e)}),
            status=500,
            mimetype='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )

# ─── Startup ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Prime both caches before starting the server
    print('[veracious] Priming fast cache...')
    update_data = {}
    update_data.update(get_mikrotik_stats())
    with _cache_lock:
        _fast_cache['data'] = update_data

    print('[veracious] Priming slow cache...')
    slow_data = {}
    for fn in [get_pihole_stats, get_proxmox_stats, get_truenas_stats,
               get_unifi_stats, get_plex_stats, get_ha_stats,
               get_portainer_stats, get_ollama_stats, get_openwebui_stats,
               get_grafana_stats,
               # Media & messaging
               get_bluebubbles_stats, get_immich_stats,
               # Game servers
               get_amp_stats,
               # 3D printers
               get_octoprint_stats, get_moonraker_stats, get_bambu_stats, get_obico_stats]:
        slow_data.update(fn())
    with _cache_lock:
        _slow_cache['data'] = slow_data

    # Start background threads
    threading.Thread(target=update_fast_cache, daemon=True).start()
    threading.Thread(target=update_slow_cache, daemon=True).start()

    print(f'[veracious] Stats API running on port {cfg.STATS_PORT}')
    app.run(host='0.0.0.0', port=cfg.STATS_PORT)
