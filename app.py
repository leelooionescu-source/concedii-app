import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from utils import zile_lucratoare, sarbatori_legale, get_sarbatori_set
from storage import (
    get_angajati, add_angajat, update_angajat, delete_angajat, get_angajat_by_id,
    get_concedii, add_concediu, delete_concediu, get_concedii_by_angajat, init_storage,
)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'concedii-app-secret-2026')

# Initialize Supabase storage
with app.app_context():
    init_storage()

TIPURI_CONCEDIU = {
    'CO': 'Concediu de odihna',
    'MEDICAL': 'Concediu medical',
    'FARA_PLATA': 'Concediu fara plata',
    'EVENIMENT': 'Eveniment (casatorie/deces/nastere)',
}


# ============ DASHBOARD ============

@app.route('/')
def dashboard():
    azi = date.today()
    an = azi.year
    angajati = [a for a in get_angajati() if a.get('activ', True)]
    angajati.sort(key=lambda a: a.get('nume', ''))
    concedii = get_concedii()

    # Cine e in concediu azi
    azi_str = azi.isoformat()
    in_concediu = []
    for c in concedii:
        if c['data_start'] <= azi_str <= c['data_sfarsit']:
            ang = get_angajat_by_id(c['angajat_id'])
            if ang:
                in_concediu.append({**c, '_angajat': ang})

    # Sold per angajat
    solduri = []
    for a in angajati:
        co_consumat = sum(
            c['zile_lucratoare'] for c in concedii
            if c['angajat_id'] == a['id'] and c['tip'] == 'CO' and c['data_start'][:4] == str(an)
        )
        solduri.append({
            'angajat': a,
            'total': a.get('zile_co_an', 21),
            'consumat': co_consumat,
            'ramas': a.get('zile_co_an', 21) - co_consumat,
        })

    return render_template('dashboard.html',
        angajati=angajati, in_concediu=in_concediu,
        solduri=solduri, azi=azi, an=an, tipuri=TIPURI_CONCEDIU)


# ============ ANGAJATI ============

@app.route('/angajati')
def lista_angajati():
    angajati = get_angajati()
    angajati.sort(key=lambda a: (not a.get('activ', True), a.get('nume', '')))
    return render_template('angajati.html', angajati=angajati)


@app.route('/angajati/adauga', methods=['POST'])
def adauga_angajat():
    nume = request.form.get('nume', '').strip()
    prenume = request.form.get('prenume', '').strip()
    departament = request.form.get('departament', '').strip()
    zile_co = request.form.get('zile_co_an', '21')
    data_ang = request.form.get('data_angajare', '')

    if not nume or not prenume:
        flash('Numele si prenumele sunt obligatorii!', 'error')
        return redirect(url_for('lista_angajati'))

    add_angajat({
        'nume': nume, 'prenume': prenume, 'departament': departament,
        'zile_co_an': int(zile_co) if zile_co else 21,
        'data_angajare': data_ang if data_ang else '',
    })
    flash(f'Angajat {prenume} {nume} adaugat.', 'success')
    return redirect(url_for('lista_angajati'))


@app.route('/angajati/editeaza/<int:id>', methods=['POST'])
def editeaza_angajat(id):
    updates = {
        'nume': request.form.get('nume', '').strip(),
        'prenume': request.form.get('prenume', '').strip(),
        'departament': request.form.get('departament', '').strip(),
        'activ': request.form.get('activ') == 'on',
    }
    zile_co = request.form.get('zile_co_an', '')
    if zile_co:
        updates['zile_co_an'] = int(zile_co)
    data_ang = request.form.get('data_angajare', '')
    if data_ang:
        updates['data_angajare'] = data_ang
    update_angajat(id, updates)
    flash('Angajat actualizat.', 'success')
    return redirect(url_for('lista_angajati'))


@app.route('/angajati/sterge/<int:id>', methods=['POST'])
def sterge_angajat(id):
    delete_angajat(id)
    flash('Angajat sters.', 'success')
    return redirect(url_for('lista_angajati'))


# ============ CONCEDII ============

@app.route('/concedii')
def lista_concedii():
    an = request.args.get('an', date.today().year, type=int)
    angajat_id = request.args.get('angajat_id', 0, type=int)

    concedii = get_concedii()
    # Filter by year
    concedii = [c for c in concedii if c['data_start'][:4] == str(an)]
    if angajat_id:
        concedii = [c for c in concedii if c['angajat_id'] == angajat_id]
    concedii.sort(key=lambda c: c['data_start'], reverse=True)

    # Attach angajat info
    for c in concedii:
        c['_angajat'] = get_angajat_by_id(c['angajat_id'])

    angajati = [a for a in get_angajati() if a.get('activ', True)]
    angajati.sort(key=lambda a: a.get('nume', ''))
    return render_template('concedii.html',
        concedii=concedii, angajati=angajati, an=an,
        angajat_id=angajat_id, tipuri=TIPURI_CONCEDIU)


@app.route('/concedii/adauga', methods=['POST'])
def adauga_concediu():
    angajat_id = request.form.get('angajat_id', type=int)
    tip = request.form.get('tip', 'CO')
    data_start = request.form.get('data_start', '')
    data_sfarsit = request.form.get('data_sfarsit', '')
    observatii = request.form.get('observatii', '').strip()

    if not angajat_id or not data_start or not data_sfarsit:
        flash('Toate campurile sunt obligatorii!', 'error')
        return redirect(url_for('lista_concedii'))

    ds = datetime.strptime(data_start, '%Y-%m-%d').date()
    de = datetime.strptime(data_sfarsit, '%Y-%m-%d').date()

    if ds > de:
        flash('Data start nu poate fi dupa data sfarsit!', 'error')
        return redirect(url_for('lista_concedii'))

    zile = zile_lucratoare(ds, de)

    add_concediu({
        'angajat_id': angajat_id, 'data_start': data_start, 'data_sfarsit': data_sfarsit,
        'tip': tip, 'zile_lucratoare': zile, 'observatii': observatii,
    })
    flash(f'Concediu adaugat: {zile} zile lucratoare.', 'success')
    return redirect(url_for('lista_concedii'))


@app.route('/concedii/sterge/<int:id>', methods=['POST'])
def sterge_concediu(id):
    delete_concediu(id)
    flash('Concediu sters.', 'success')
    return redirect(url_for('lista_concedii'))


# ============ CALENDAR ============

@app.route('/calendar')
def calendar_view():
    an = request.args.get('an', date.today().year, type=int)
    luna = request.args.get('luna', date.today().month, type=int)

    sarbatori = get_sarbatori_set(an)
    sarbatori_dict = {s[0]: s[1] for s in sarbatori_legale(an)}

    prima_zi = date(an, luna, 1)
    if luna == 12:
        ultima_zi = date(an, 12, 31)
    else:
        ultima_zi = date(an, luna + 1, 1) - timedelta(days=1)

    concedii = get_concedii()
    # Filter concedii that overlap this month
    prima_str = prima_zi.isoformat()
    ultima_str = ultima_zi.isoformat()
    concedii_luna = [c for c in concedii if c['data_start'] <= ultima_str and c['data_sfarsit'] >= prima_str]
    for c in concedii_luna:
        c['_angajat'] = get_angajat_by_id(c['angajat_id'])

    zile = []
    d = prima_zi
    while d <= ultima_zi:
        d_str = d.isoformat()
        zi_info = {
            'data': d,
            'weekend': d.weekday() >= 5,
            'sarbatoare': sarbatori_dict.get(d, ''),
            'concedii': [c for c in concedii_luna if c['data_start'] <= d_str <= c['data_sfarsit']],
        }
        zile.append(zi_info)
        d += timedelta(days=1)

    luni_nume = ['', 'Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
                 'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']

    return render_template('calendar.html',
        zile=zile, an=an, luna=luna, luna_nume=luni_nume[luna],
        tipuri=TIPURI_CONCEDIU)


# ============ SARBATORI ============

@app.route('/sarbatori')
def lista_sarbatori():
    an = request.args.get('an', date.today().year, type=int)
    sarb = sarbatori_legale(an)
    sarbatori_list = [{'data': s[0], 'denumire': s[1]} for s in sarb]
    return render_template('sarbatori.html', sarbatori=sarbatori_list, an=an)


# ============ RAPOARTE ============

@app.route('/rapoarte/export')
def export_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    import tempfile

    an = request.args.get('an', date.today().year, type=int)
    angajati = [a for a in get_angajati() if a.get('activ', True)]
    angajati.sort(key=lambda a: a.get('nume', ''))
    concedii = get_concedii()

    wb = Workbook()
    ws = wb.active
    ws.title = f'Concedii {an}'

    headers = ['Nr.', 'Prenume', 'Nume', 'Departament', 'Zile CO/an',
               'CO consumat', 'CO ramas', 'Medical', 'Fara plata', 'Eveniment', 'Total zile']
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'))

    for j, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=j, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    for i, a in enumerate(angajati, 1):
        ang_concedii = [c for c in concedii if c['angajat_id'] == a['id'] and c['data_start'][:4] == str(an)]
        co = sum(c['zile_lucratoare'] for c in ang_concedii if c['tip'] == 'CO')
        med = sum(c['zile_lucratoare'] for c in ang_concedii if c['tip'] == 'MEDICAL')
        fp = sum(c['zile_lucratoare'] for c in ang_concedii if c['tip'] == 'FARA_PLATA')
        ev = sum(c['zile_lucratoare'] for c in ang_concedii if c['tip'] == 'EVENIMENT')
        zile_co_an = a.get('zile_co_an', 21)
        vals = [i, a.get('prenume', ''), a.get('nume', ''), a.get('departament', ''),
                zile_co_an, co, zile_co_an - co, med, fp, ev, co + med + fp + ev]
        for j, v in enumerate(vals, 1):
            cell = ws.cell(row=i + 1, column=j, value=v)
            cell.border = thin_border
            if j >= 5:
                cell.alignment = Alignment(horizontal='center')

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    filepath = os.path.join(tempfile.gettempdir(), f'Concedii_{an}.xlsx')
    wb.save(filepath)
    return send_file(filepath, as_attachment=True, download_name=f'Raport Concedii {an}.xlsx')


# ============ API NOTIFICARI ============

@app.route('/api/notifications')
def api_notifications():
    azi = date.today()
    maine = azi + timedelta(days=1)
    azi_str = azi.isoformat()
    maine_str = maine.isoformat()
    notificari = []
    concedii = get_concedii()
    angajati = get_angajati()

    for c in concedii:
        ang = next((a for a in angajati if a['id'] == c['angajat_id'] and a.get('activ', True)), None)
        if not ang:
            continue
        nume = f"{ang.get('prenume', '')} {ang.get('nume', '')}"
        if c['data_start'] == maine_str:
            notificari.append({
                'title': 'Concediu incepe maine',
                'body': f'{nume} - {TIPURI_CONCEDIU.get(c["tip"], c["tip"])} ({c["zile_lucratoare"]} zile)',
            })
        if c['data_sfarsit'] == azi_str:
            notificari.append({
                'title': 'Revine din concediu',
                'body': f'{nume} revine maine la lucru',
            })

    an = azi.year
    for a in angajati:
        if not a.get('activ', True):
            continue
        co = sum(c['zile_lucratoare'] for c in concedii
                 if c['angajat_id'] == a['id'] and c['tip'] == 'CO' and c['data_start'][:4] == str(an))
        ramas = a.get('zile_co_an', 21) - co
        if 0 < ramas <= 3:
            notificari.append({
                'title': 'Sold CO scazut',
                'body': f'{a.get("prenume", "")} {a.get("nume", "")} mai are doar {ramas} zile CO',
            })

    return jsonify(notificari)


# ============ RUN ============

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5080, debug=False)
