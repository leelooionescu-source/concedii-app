"""Supabase Storage backend - salveaza/citeste date JSON in cloud.
Foloseste acelasi proiect Supabase ca remi-scoreboard."""
import os
import json
import requests
from datetime import date, datetime

SUPABASE_URL = "https://lbpuuvujpxtwwmdnlhvh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BUCKET = "concedii"

HEADERS = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
}


def _ensure_bucket():
    """Creaza bucket-ul daca nu exista."""
    try:
        r = requests.post(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"id": BUCKET, "name": BUCKET, "public": True},
            timeout=10,
        )
    except Exception:
        pass


def _read_json(filename, default=None):
    """Citeste JSON din Supabase Storage."""
    if default is None:
        default = []
    try:
        r = requests.get(
            f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}?t={datetime.now().timestamp()}",
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return default


def _write_json(filename, data):
    """Scrie JSON in Supabase Storage."""
    try:
        r = requests.put(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}",
            headers={**HEADERS, "Content-Type": "application/json", "x-upsert": "true"},
            data=json.dumps(data, ensure_ascii=False, default=str),
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


# ============ ANGAJATI ============

def get_angajati():
    return _read_json("angajati.json", [])


def save_angajati(angajati):
    return _write_json("angajati.json", angajati)


def add_angajat(data):
    angajati = get_angajati()
    max_id = max((a.get('id', 0) for a in angajati), default=0)
    data['id'] = max_id + 1
    data['activ'] = True
    data['created_at'] = datetime.now().isoformat()
    angajati.append(data)
    save_angajati(angajati)
    return data


def update_angajat(id, updates):
    angajati = get_angajati()
    for a in angajati:
        if a['id'] == id:
            a.update(updates)
            break
    save_angajati(angajati)


def delete_angajat(id):
    angajati = get_angajati()
    angajati = [a for a in angajati if a['id'] != id]
    save_angajati(angajati)
    # Also delete related concedii
    concedii = get_concedii()
    concedii = [c for c in concedii if c['angajat_id'] != id]
    save_concedii(concedii)


def get_angajat_by_id(id):
    for a in get_angajati():
        if a['id'] == id:
            return a
    return None


# ============ CONCEDII ============

def get_concedii():
    return _read_json("concedii.json", [])


def save_concedii(concedii):
    return _write_json("concedii.json", concedii)


def add_concediu(data):
    concedii = get_concedii()
    max_id = max((c.get('id', 0) for c in concedii), default=0)
    data['id'] = max_id + 1
    data['created_at'] = datetime.now().isoformat()
    concedii.append(data)
    save_concedii(concedii)
    return data


def delete_concediu(id):
    concedii = get_concedii()
    concedii = [c for c in concedii if c['id'] != id]
    save_concedii(concedii)


def get_concedii_by_angajat(angajat_id, an=None):
    concedii = get_concedii()
    result = [c for c in concedii if c['angajat_id'] == angajat_id]
    if an:
        result = [c for c in result if c['data_start'][:4] == str(an)]
    return result


def init_storage():
    """Initializeaza storage-ul Supabase."""
    _ensure_bucket()
    # Daca nu exista fisiere, creaza-le goale
    if not get_angajati():
        save_angajati([])
    if not get_concedii():
        save_concedii([])
