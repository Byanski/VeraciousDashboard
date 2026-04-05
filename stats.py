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

from flask import Flask
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

def get_pihole_stats():
    if not cfg.PIHOLE_ENABLED:
        return {}
    try:
        auth = requests.post(
            f'{cfg.PIHOLE_HOST}/api/auth',
            json={'password': cfg.PIHOLE_PASS},
            timeout=5
        )
        sid = auth.json()['session']['sid']

        res = requests.get(
            f'{cfg.PIHOLE_HOST}/api/stats/summary',
            cookies={'sid': sid},
            timeout=5
        )
        data = res.json()

        requests.delete(
            f'{cfg.PIHOLE_HOST}/api/auth',
            cookies={'sid': sid},
            timeout=5
        )

        return {
            'pihole_blocked':       data['queries']['blocked'],
            'pihole_percent':       round(data['queries']['percent_blocked'], 1),
            'pihole_total':         data['queries']['total'],
            'pihole_gravity':       data['gravity']['domains_being_blocked'],
        }
    except Exception as e:
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
               get_grafana_stats]:
        slow_data.update(fn())
    with _cache_lock:
        _slow_cache['data'] = slow_data

    # Start background threads
    threading.Thread(target=update_fast_cache, daemon=True).start()
    threading.Thread(target=update_slow_cache, daemon=True).start()

    print(f'[veracious] Stats API running on port {cfg.STATS_PORT}')
    app.run(host='0.0.0.0', port=cfg.STATS_PORT)
