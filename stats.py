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
            'mikrotik_up_mbps':   round(max(tx_speed, 0), 2),
            'mikrotik_down_mbps': round(max(rx_speed, 0), 2),
            'mikrotik_devices':   len(active_leases),
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
            'pihole_blocked': data['queries']['blocked'],
            'pihole_percent': round(data['queries']['percent_blocked'], 1),
            'pihole_total':   data['queries']['total'],
            'pihole_gravity': data['gravity']['domains_being_blocked'],
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
            'proxmox_cpu_pct': round(data['cpu'] * 100, 1),
            'proxmox_mem_pct': round(data['memory']['used'] / data['memory']['total'] * 100, 1),
            'proxmox_vms':     running_vms,
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
            'truenas_pools':   len(pools),
            'truenas_healthy': 'Yes' if healthy else 'No',
            'truenas_disks':   disk_count,
        }
    except Exception as e:
        return {'truenas_error': str(e)}


# ─── Synology DSM ─────────────────────────────────────────────────────────────
# Tested against DSM 7.x. Uses the SYNO.API.Auth + SYNO.FileStation.Info APIs.
# No additional packages required — plain HTTP requests.

def get_synology_stats():
    if not cfg.SYNOLOGY_ENABLED:
        return {}
    try:
        # Authenticate and get a session ID
        auth = requests.get(
            f'{cfg.SYNOLOGY_HOST}/webapi/auth.cgi',
            params={
                'api':     'SYNO.API.Auth',
                'version': '3',
                'method':  'login',
                'account': cfg.SYNOLOGY_USER,
                'passwd':  cfg.SYNOLOGY_PASS,
                'session': 'dashboard',
                'format':  'sid',
            },
            verify=False,
            timeout=5
        )
        sid = auth.json()['data']['sid']

        # Storage info
        storage = requests.get(
            f'{cfg.SYNOLOGY_HOST}/webapi/entry.cgi',
            params={
                'api':     'SYNO.Storage.CGI.Storage',
                'version': '1',
                'method':  'load_info',
                '_sid':    sid,
            },
            verify=False,
            timeout=5
        ).json()

        volumes   = storage.get('data', {}).get('volumes', [])
        vol_count = len(volumes)
        # Aggregate used/total across all volumes (bytes → GB)
        total_gb = sum(v.get('size', {}).get('total', 0) for v in volumes) / 1024**3
        used_gb  = sum(v.get('size', {}).get('used', 0)  for v in volumes) / 1024**3
        used_pct = round(used_gb / total_gb * 100, 1) if total_gb > 0 else 0

        # Logout
        requests.get(
            f'{cfg.SYNOLOGY_HOST}/webapi/auth.cgi',
            params={'api': 'SYNO.API.Auth', 'version': '1', 'method': 'logout', '_sid': sid},
            verify=False, timeout=5
        )

        return {
            'synology_volumes':  vol_count,
            'synology_used_pct': used_pct,
            'synology_used_gb':  round(used_gb, 1),
            'synology_total_gb': round(total_gb, 1),
        }
    except Exception as e:
        return {'synology_error': str(e)}


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


# ─── Jellyfin ─────────────────────────────────────────────────────────────────
# Uses the Jellyfin REST API. API key generated in Dashboard > API Keys.

def get_jellyfin_stats():
    if not cfg.JELLYFIN_ENABLED:
        return {}
    try:
        headers = {'X-Emby-Token': cfg.JELLYFIN_API_KEY}

        sessions = requests.get(
            f'{cfg.JELLYFIN_HOST}/Sessions',
            headers=headers,
            timeout=5
        ).json()
        active_streams = len([s for s in sessions if s.get('NowPlayingItem')])

        libraries = requests.get(
            f'{cfg.JELLYFIN_HOST}/Library/VirtualFolders',
            headers=headers,
            timeout=5
        ).json()

        return {
            'jellyfin_streams':   active_streams,
            'jellyfin_libraries': len(libraries),
        }
    except Exception as e:
        return {'jellyfin_error': str(e)}


# ─── Emby ─────────────────────────────────────────────────────────────────────
# Uses the Emby REST API. API key generated in Dashboard > Advanced > API Keys.

def get_emby_stats():
    if not cfg.EMBY_ENABLED:
        return {}
    try:
        headers = {'X-Emby-Token': cfg.EMBY_API_KEY}

        sessions = requests.get(
            f'{cfg.EMBY_HOST}/Sessions',
            headers=headers,
            timeout=5
        ).json()
        active_streams = len([s for s in sessions if s.get('NowPlayingItem')])

        libraries = requests.get(
            f'{cfg.EMBY_HOST}/Library/VirtualFolders',
            headers=headers,
            timeout=5
        ).json()

        return {
            'emby_streams':   active_streams,
            'emby_libraries': len(libraries),
        }
    except Exception as e:
        return {'emby_error': str(e)}


# ─── Audiobookshelf ───────────────────────────────────────────────────────────
# Uses the Audiobookshelf REST API. API token found in Settings > Users.

def get_audiobookshelf_stats():
    if not cfg.AUDIOBOOKSHELF_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.AUDIOBOOKSHELF_TOKEN}'}

        libraries = requests.get(
            f'{cfg.AUDIOBOOKSHELF_HOST}/api/libraries',
            headers=headers,
            timeout=5
        ).json().get('libraries', [])

        sessions = requests.get(
            f'{cfg.AUDIOBOOKSHELF_HOST}/api/users/online',
            headers=headers,
            timeout=5
        ).json()
        active = len(sessions.get('openSessions', []))

        return {
            'audiobookshelf_libraries': len(libraries),
            'audiobookshelf_active':    active,
        }
    except Exception as e:
        return {'audiobookshelf_error': str(e)}


# ─── Navidrome ────────────────────────────────────────────────────────────────
# Uses the Subsonic-compatible API built into Navidrome.
# Credentials are your Navidrome username/password.

def get_navidrome_stats():
    if not cfg.NAVIDROME_ENABLED:
        return {}
    try:
        import hashlib, secrets as _secrets
        salt   = _secrets.token_hex(6)
        token  = hashlib.md5(f'{cfg.NAVIDROME_PASS}{salt}'.encode()).hexdigest()

        params = {
            'u': cfg.NAVIDROME_USER, 't': token, 's': salt,
            'v': '1.16.0', 'c': 'veracious', 'f': 'json'
        }

        artists = requests.get(
            f'{cfg.NAVIDROME_HOST}/rest/getArtists',
            params=params, timeout=5
        ).json()
        artist_count = len(
            artists.get('subsonic-response', {})
                   .get('artists', {})
                   .get('index', [])
        )

        songs = requests.get(
            f'{cfg.NAVIDROME_HOST}/rest/getRandomSongs',
            params={**params, 'size': '1'}, timeout=5
        ).json()
        song_count = songs.get('subsonic-response', {}).get('randomSongs', {}).get('song', [])

        playlists = requests.get(
            f'{cfg.NAVIDROME_HOST}/rest/getPlaylists',
            params=params, timeout=5
        ).json().get('subsonic-response', {}).get('playlists', {}).get('playlist', [])

        return {
            'navidrome_artists':   artist_count,
            'navidrome_playlists': len(playlists),
        }
    except Exception as e:
        return {'navidrome_error': str(e)}


# ─── Immich ───────────────────────────────────────────────────────────────────
# Uses the Immich REST API. API key generated in Account Settings > API Keys.

def get_immich_stats():
    if not cfg.IMMICH_ENABLED:
        return {}
    try:
        headers = {'x-api-key': cfg.IMMICH_API_KEY}

        stats = requests.get(
            f'{cfg.IMMICH_HOST}/api/server-info/statistics',
            headers=headers,
            timeout=5
        ).json()

        return {
            'immich_photos': stats.get('photos', 0),
            'immich_videos': stats.get('videos', 0),
            'immich_usage_gb': round(stats.get('usage', 0) / 1024**3, 1),
        }
    except Exception as e:
        return {'immich_error': str(e)}


# ─── Nextcloud ────────────────────────────────────────────────────────────────
# Uses the Nextcloud Server Info API (requires the serverinfo app, enabled by default).
# AUTH: basic auth with admin credentials or an app password (recommended).

def get_nextcloud_stats():
    if not cfg.NEXTCLOUD_ENABLED:
        return {}
    try:
        res = requests.get(
            f'{cfg.NEXTCLOUD_HOST}/ocs/v2.php/apps/serverinfo/api/v1/info?format=json',
            auth=(cfg.NEXTCLOUD_USER, cfg.NEXTCLOUD_PASS),
            headers={'OCS-APIRequest': 'true'},
            timeout=5
        )
        data = res.json()['ocs']['data']

        return {
            'nextcloud_users':   data['activeUsers']['last24hours'],
            'nextcloud_files':   data['nextcloud']['storage']['num_files'],
            'nextcloud_used_gb': round(data['nextcloud']['storage']['used'] / 1024**3, 1),
        }
    except Exception as e:
        return {'nextcloud_error': str(e)}


# ─── Vaultwarden ──────────────────────────────────────────────────────────────
# Uses the Vaultwarden admin API. Requires ADMIN_TOKEN set in Vaultwarden config.
# Only exposes user count — no sensitive vault data is accessed.

def get_vaultwarden_stats():
    if not cfg.VAULTWARDEN_ENABLED:
        return {}
    try:
        res = requests.get(
            f'{cfg.VAULTWARDEN_HOST}/admin/users/overview',
            headers={'Authorization': f'Bearer {cfg.VAULTWARDEN_ADMIN_TOKEN}'},
            timeout=5
        )
        users = res.json()
        return {
            'vaultwarden_users': len(users),
        }
    except Exception as e:
        return {'vaultwarden_error': str(e)}


# ─── BlueBubbles ──────────────────────────────────────────────────────────────
# Uses the BlueBubbles REST API. Password is set in BlueBubbles Server settings.

def get_bluebubbles_stats():
    if not cfg.BLUEBUBBLES_ENABLED:
        return {}
    try:
        params = {'password': cfg.BLUEBUBBLES_PASS}

        info = requests.get(
            f'{cfg.BLUEBUBBLES_HOST}/api/v1/server/info',
            params=params, timeout=5
        ).json().get('data', {})

        chats = requests.get(
            f'{cfg.BLUEBUBBLES_HOST}/api/v1/chat/count',
            params=params, timeout=5
        ).json().get('data', {})

        return {
            'bluebubbles_chats':   chats.get('total', 0),
            'bluebubbles_version': info.get('server_version', '?'),
        }
    except Exception as e:
        return {'bluebubbles_error': str(e)}


# ─── Mealie ───────────────────────────────────────────────────────────────────
# Uses the Mealie REST API. API token generated in User Settings > API Tokens.

def get_mealie_stats():
    if not cfg.MEALIE_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.MEALIE_TOKEN}'}

        recipes = requests.get(
            f'{cfg.MEALIE_HOST}/api/recipes',
            headers=headers,
            params={'perPage': 1},
            timeout=5
        ).json()

        meal_plans = requests.get(
            f'{cfg.MEALIE_HOST}/api/groups/mealplans/today',
            headers=headers,
            timeout=5
        ).json()

        return {
            'mealie_recipes':   recipes.get('total', 0),
            'mealie_today':     len(meal_plans) if isinstance(meal_plans, list) else 0,
        }
    except Exception as e:
        return {'mealie_error': str(e)}


# ─── Home Assistant ───────────────────────────────────────────────────────────

def get_ha_stats():
    if not cfg.HA_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.HA_TOKEN}'}
        states = requests.get(
            f'{cfg.HA_HOST}/api/states',
            headers=headers,
            timeout=5
        ).json()

        entity_count = len(states)
        automations  = len([s for s in states if s['entity_id'].startswith('automation.')])

        return {
            'ha_entities':    entity_count,
            'ha_automations': automations,
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
            'portainer_running': running,
            'portainer_total':   total,
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
        data.update(get_synology_stats())
        data.update(get_unifi_stats())
        data.update(get_plex_stats())
        data.update(get_jellyfin_stats())
        data.update(get_emby_stats())
        data.update(get_audiobookshelf_stats())
        data.update(get_navidrome_stats())
        data.update(get_immich_stats())
        data.update(get_nextcloud_stats())
        data.update(get_vaultwarden_stats())
        data.update(get_bluebubbles_stats())
        data.update(get_mealie_stats())
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

_all_slow_fns = [
    get_pihole_stats, get_proxmox_stats, get_truenas_stats,
    get_synology_stats, get_unifi_stats, get_plex_stats,
    get_jellyfin_stats, get_emby_stats, get_audiobookshelf_stats,
    get_navidrome_stats, get_immich_stats, get_nextcloud_stats,
    get_vaultwarden_stats, get_bluebubbles_stats, get_mealie_stats,
    get_ha_stats, get_portainer_stats, get_ollama_stats,
    get_openwebui_stats, get_grafana_stats,
]

if __name__ == '__main__':
    # Prime both caches before starting the server
    print('[veracious] Priming fast cache...')
    update_data = {}
    update_data.update(get_mikrotik_stats())
    with _cache_lock:
        _fast_cache['data'] = update_data

    print('[veracious] Priming slow cache...')
    slow_data = {}
    for fn in _all_slow_fns:
        slow_data.update(fn())
    with _cache_lock:
        _slow_cache['data'] = slow_data

    # Start background threads
    threading.Thread(target=update_fast_cache, daemon=True).start()
    threading.Thread(target=update_slow_cache, daemon=True).start()

    print(f'[veracious] Stats API running on port {cfg.STATS_PORT}')
    app.run(host='0.0.0.0', port=cfg.STATS_PORT)
