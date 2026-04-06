"""Utilitare: calcul zile lucratoare, sarbatori legale Romania (Codul Muncii Art. 139)."""
from datetime import date, timedelta


def _paste_ortodox(an):
    """Calculeaza data Pastelui Ortodox pentru un an dat (algoritm Meeus)."""
    a = an % 4
    b = an % 7
    c = an % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    luna = (d + e + 114) // 31
    zi = ((d + e + 114) % 31) + 1
    # Convertire din calendar iulian la gregorian (+13 zile pt sec. 20-21)
    julian = date(an, luna, zi)
    return julian + timedelta(days=13)


def sarbatori_legale(an):
    """Returneaza lista de sarbatori legale Romania pentru un an dat.
    Conform Codului Muncii Art. 139."""
    paste = _paste_ortodox(an)
    vinerea_mare = paste - timedelta(days=2)
    rusalii_d = paste + timedelta(days=49)  # Duminica Rusaliilor
    rusalii_l = paste + timedelta(days=50)  # Lunea Rusaliilor

    sarbatori = [
        (date(an, 1, 1), "Anul Nou"),
        (date(an, 1, 2), "Anul Nou (ziua 2)"),
        (date(an, 1, 24), "Ziua Unirii Principatelor Romane"),
        (vinerea_mare, "Vinerea Mare"),
        (paste, "Pastele Ortodox (Duminica)"),
        (paste + timedelta(days=1), "Pastele Ortodox (Luni)"),
        (date(an, 5, 1), "Ziua Muncii"),
        (date(an, 6, 1), "Ziua Copilului"),
        (rusalii_d, "Rusalii (Duminica)"),
        (rusalii_l, "Rusalii (Luni)"),
        (date(an, 8, 15), "Adormirea Maicii Domnului"),
        (date(an, 11, 30), "Sfantul Andrei"),
        (date(an, 12, 1), "Ziua Nationala a Romaniei"),
        (date(an, 12, 25), "Craciunul (ziua 1)"),
        (date(an, 12, 26), "Craciunul (ziua 2)"),
    ]
    return sarbatori


def get_sarbatori_set(an):
    """Returneaza set de date (sarbatori legale) pentru un an."""
    return {s[0] for s in sarbatori_legale(an)}


def zile_lucratoare(data_start, data_sfarsit, sarbatori_extra=None):
    """Calculeaza numarul de zile lucratoare intre doua date (inclusiv).
    Exclude weekenduri si sarbatori legale."""
    if data_start > data_sfarsit:
        return 0

    ani = set()
    d = data_start
    while d <= data_sfarsit:
        ani.add(d.year)
        d += timedelta(days=1)

    sarbatori = set()
    for an in ani:
        sarbatori.update(get_sarbatori_set(an))
    if sarbatori_extra:
        sarbatori.update(sarbatori_extra)

    count = 0
    d = data_start
    while d <= data_sfarsit:
        if d.weekday() < 5 and d not in sarbatori:  # Luni-Vineri, nu sarbatoare
            count += 1
        d += timedelta(days=1)
    return count


def sold_co(angajat, an, concedii_list):
    """Calculeaza soldul de zile CO ramase pentru un angajat intr-un an."""
    total = angajat.zile_co_an
    consumate = sum(
        c.zile_lucratoare for c in concedii_list
        if c.tip == 'CO' and c.data_start.year == an
    )
    return total - consumate
