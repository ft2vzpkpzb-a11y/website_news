#!/usr/bin/env python3
"""Baut aus den Artikeln im Ordner artikel/ die Seiten des Newsportals.

Aufruf (im Projektordner):
  python3 werkzeuge/artikel_bauen.py            alles neu bauen
  python3 werkzeuge/artikel_bauen.py --pruefen  nur prüfen und melden, nichts schreiben

Was entsteht (alles in public/, also das, was auf den Server kommt):
  <adresse>.html   je Artikel eine Seite; die Adresse ist der Dateiname ohne .txt
                   (artikel/budget-2027.txt wird zu /budget-2027)
  <rubrik>.html    je Rubrik eine Übersichtsseite (/politik, /wirtschaft …)
  index.html       nur der Bereich zwischen <!-- AUTO:startseite --> und
                   <!-- /AUTO:startseite -->; der Rest der Startseite bleibt, wie er ist
  sitemap.xml      alle Seiten für Suchmaschinen; robots.txt nennt sie

Rubriken, Name und Domain stehen in werkzeuge/portal.json, die Vorlagen für
Artikel und Rubriken in werkzeuge/vorlagen/. Kopfzeile, Fußzeile und
Cookie-Fenster übernimmt das Programm aus index.html, genau so, wie es
seiten_abgleichen.py im Skill website-bauen tut (Menüpunkt der Rubrik markiert).
Darum gilt weiter: gemeinsame Teile nur in index.html ändern, dann zuerst
seiten_abgleichen.py und danach dieses Programm laufen lassen.

Erzeugte Seiten tragen im Kopf einen Vermerk. Wird ein Artikel gelöscht, löscht
das Programm auch seine Seite, aber nie eine Seite ohne diesen Vermerk.

Wie eine Artikeldatei aussieht: artikel/ANLEITUNG.md

Nur Python 3 mit Standardbibliothek, keine Pakete.
"""
import argparse
import datetime
import html
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True

WERKZEUGE = Path(__file__).resolve().parent
PROJEKT = WERKZEUGE.parent
PUBLIC = PROJEKT / 'public'
ARTIKEL = PROJEKT / 'artikel'
VORLAGEN = WERKZEUGE / 'vorlagen'
EINSTELLUNGEN = WERKZEUGE / 'portal.json'

VERMERK = '<!-- ERZEUGT von werkzeuge/artikel_bauen.py aus {quelle}. Nicht von Hand ändern: Änderungen gehen beim nächsten Bauen verloren. -->'
VERMERK_RE = re.compile(r'<!-- ERZEUGT von werkzeuge/artikel_bauen\.py')
AUTO_RE = re.compile(r'(<!-- AUTO:startseite -->)(.*?)(\n?[ \t]*<!-- /AUTO:startseite -->)', re.S)

MONATE = ['Jänner', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']
FESTE_SEITEN = {'index', '404', 'kontakt', 'impressum', 'datenschutz'}
ADRESSE_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
FELDER = {
    'titel': 'Titel', 'dachzeile': 'Dachzeile', 'rubrik': 'Rubrik', 'datum': 'Datum',
    'aktualisiert': 'Aktualisiert', 'autor': 'Autor', 'vorspann': 'Vorspann',
    'beschreibung': 'Beschreibung', 'bild': 'Bild', 'bildtext': 'Bildtext',
    'bildnachweis': 'Bildnachweis', 'aufmacher': 'Aufmacher',
}
PFLICHT = ('titel', 'rubrik', 'datum', 'vorspann')

KAMERA = ('<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4V8Z" '
          'stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><circle cx="12" cy="13" r="3.5" '
          'stroke="currentColor" stroke-width="1.5"/></svg>')
PFEIL = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" '
         'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


class Fehler(Exception):
    pass


def esc(text):
    return html.escape(text or '', quote=True)


# ---------- Gemeinsame Teile (wie seiten_abgleichen.py im Skill website-bauen) ----------

BLOCK_RE = re.compile(r'<!-- GEMEINSAM:([a-z0-9-]+) -->(.*?)<!-- /GEMEINSAM:\1 -->', re.S)
NAV_RE = re.compile(r'(<nav\b[^>]*\bclass="[^"]*\bmain-nav\b[^"]*"[^>]*>)(.*?)(</nav>)', re.S)
A_RE = re.compile(r'<a\b([^>]*)>')


def normal(href):
    href = href.split('#')[0].split('?')[0]
    href = re.sub(r'\.html$', '', href)
    if href in ('/index', ''):
        return '/'
    return href.rstrip('/') or '/'


def _ohne_aktiv(attrs):
    attrs = re.sub(r'\s+aria-current="page"', '', attrs)

    def klasse(m):
        rest = ' '.join(k for k in m.group(1).split() if k != 'is-active')
        return f' class="{rest}"' if rest else ''
    return re.sub(r'\s+class="([^"]*)"', klasse, attrs)


def menue_setzen(block, aktiv):
    """Entfernt alle Markierungen im Menü und setzt sie (falls aktiv angegeben) neu."""
    def nav(m):
        def link(a):
            attrs = _ohne_aktiv(a.group(1))
            href = re.search(r'\bhref="([^"]*)"', attrs)
            ist_knopf = re.search(r'\bclass="[^"]*\bbtn\b', attrs)
            if aktiv and href and not ist_knopf and href.group(1).startswith('/') and normal(href.group(1)) == aktiv:
                if re.search(r'\bclass="', attrs):
                    attrs = re.sub(r'\bclass="([^"]*)"', lambda c: f'class="{c.group(1)} is-active"', attrs, count=1)
                else:
                    attrs += ' class="is-active"'
                attrs += ' aria-current="page"'
            return f'<a{attrs}>'
        return m.group(1) + A_RE.sub(link, m.group(2)) + m.group(3)
    return NAV_RE.sub(nav, block)


def gemeinsame_teile(index_text):
    teile = {name: menue_setzen(inhalt, None) for name, inhalt in BLOCK_RE.findall(index_text)}
    if not teile:
        raise Fehler('index.html enthält keine Markierungen <!-- GEMEINSAM:… -->.')
    return teile


def teile_einsetzen(text, teile, aktiv):
    def ersetzen(m):
        name = m.group(1)
        if name not in teile:
            raise Fehler(f'Vorlage enthält den Teil „{name}“, den es in index.html nicht gibt.')
        return f'<!-- GEMEINSAM:{name} -->{menue_setzen(teile[name], aktiv)}<!-- /GEMEINSAM:{name} -->'
    return BLOCK_RE.sub(ersetzen, text)


def vorlage_fuellen(vorlage, werte):
    def ersetzen(m):
        if m.group(1) not in werte:
            raise Fehler(f'Vorlage: Platzhalter {{{{{m.group(1)}}}}} hat keinen Wert.')
        return werte[m.group(1)]
    return re.sub(r'\{\{([a-z_]+)\}\}', ersetzen, vorlage)


# ---------- Artikel lesen ----------

class Artikel:
    def __init__(self, datei, felder, text):
        self.datei = datei
        self.adresse = datei.stem
        self.titel = felder['titel']
        self.dachzeile = felder.get('dachzeile', '')
        self.rubrik = felder['rubrik']
        self.datum = felder['datum']
        self.aktualisiert = felder.get('aktualisiert')
        self.autor = felder.get('autor', '')
        self.vorspann = felder['vorspann']
        self.beschreibung = felder.get('beschreibung', '')
        self.bild = felder.get('bild')
        self.bildtext = felder.get('bildtext', '')
        self.bildnachweis = felder.get('bildnachweis', '')
        self.aufmacher = felder.get('aufmacher', False)
        self.text = text


def datum_lesen(wert, wo):
    wert = ' '.join(wert.split())
    for muster in ('%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M', '%d.%m.%Y, %H:%M', '%Y-%m-%d', '%d.%m.%Y'):
        try:
            return datetime.datetime.strptime(wert, muster)
        except ValueError:
            pass
    raise Fehler(f'{wo}: Datum „{wert}“ nicht lesbar (Form: 2026-11-16 14:30 oder 16.11.2026 14:30)')


def artikel_lesen(datei, rubriken):
    wo = f'artikel/{datei.name}'
    if not ADRESSE_RE.match(datei.stem):
        raise Fehler(f'{wo}: Der Dateiname wird zur Adresse und darf nur Kleinbuchstaben, Ziffern und '
                     f'Bindestriche enthalten (ohne Umlaute, ß und Leerzeichen), z. B. budget-2027.txt')
    if datei.stem in FESTE_SEITEN or datei.stem in rubriken:
        raise Fehler(f'{wo}: Die Adresse /{datei.stem} ist schon vergeben (feste Seite oder Rubrik).')
    roh = datei.read_text(encoding='utf-8-sig').replace('\r\n', '\n').replace('\r', '\n').lstrip('\n')
    kopf, _, text = roh.partition('\n\n')
    felder, letztes = {}, None
    for nr, zeile in enumerate(kopf.split('\n'), 1):
        if not zeile.strip():
            continue
        name, doppelpunkt, wert = zeile.partition(':')
        schluessel = name.strip().lower()
        if doppelpunkt and schluessel in FELDER:
            if schluessel in felder:
                raise Fehler(f'{wo}, Zeile {nr}: „{FELDER[schluessel]}“ steht doppelt.')
            felder[schluessel] = wert.strip()
            letztes = schluessel
        elif letztes:
            felder[letztes] += ' ' + zeile.strip()       # Fortsetzung der vorigen Angabe
        else:
            raise Fehler(f'{wo}, Zeile {nr}: „{zeile.strip()}“ ist keine bekannte Angabe '
                         f'({", ".join(FELDER.values())}).')
    for pflicht in PFLICHT:
        if not felder.get(pflicht):
            raise Fehler(f'{wo}: Angabe „{FELDER[pflicht]}“ fehlt.')
    rubrik = felder['rubrik'].strip().lower()
    nach_name = {r['name'].lower(): r['adresse'] for r in rubriken.values()}
    rubrik = rubrik if rubrik in rubriken else nach_name.get(rubrik)
    if not rubrik:
        raise Fehler(f'{wo}: Rubrik „{felder["rubrik"]}“ gibt es nicht ({", ".join(r["name"] for r in rubriken.values())}).')
    felder['rubrik'] = rubrik
    felder['datum'] = datum_lesen(felder['datum'], wo)
    if felder.get('aktualisiert'):
        felder['aktualisiert'] = datum_lesen(felder['aktualisiert'], wo)
    else:
        felder.pop('aktualisiert', None)
    felder['aufmacher'] = felder.get('aufmacher', '').strip().lower() in ('ja', 'j', 'yes', 'true', '1')
    bild = felder.get('bild', '').strip()
    if not bild:
        felder['bild'] = None
    elif bild.lower() == 'platzhalter':
        felder['bild'] = 'platzhalter'
    else:
        if not bild.startswith('/assets/images/'):
            raise Fehler(f'{wo}: Bild „{bild}“: Fotos liegen in public/assets/images/…, '
                         f'angegeben wird die Adresse ab /assets/images/.')
        if not (PUBLIC / bild.lstrip('/')).is_file():
            raise Fehler(f'{wo}: Das Bild {bild} gibt es nicht (Datei in public{bild} ablegen).')
        felder['bild'] = bild
    if not text.strip():
        raise Fehler(f'{wo}: Der Artikel hat keinen Text (nach den Angaben eine Leerzeile, dann der Text).')
    return Artikel(datei, felder, text)


# ---------- Text des Artikels ----------

def inline(text):
    t = esc(text)

    def link(m):
        beschriftung, ziel = m.group(1), html.unescape(m.group(2))
        if re.match(r'https?://', ziel):
            return f'<a href="{esc(ziel)}" target="_blank" rel="noopener">{beschriftung}</a>'
        if re.fullmatch(r'/[a-z0-9-]*(#[a-z0-9-]+)?', ziel):
            return f'<a href="{esc(ziel)}">{beschriftung}</a>'
        return m.group(0)
    t = re.sub(r'(?<!\[)\[([^\[\]]+)\]\(([^)\s]+)\)', link, t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    return t


def text_html(text, einzug='        '):
    teile = []
    for block in re.split(r'\n[ \t]*\n', text.strip()):
        zeilen = [z.strip() for z in block.strip().split('\n') if z.strip()]
        if not zeilen:
            continue
        if zeilen[0].startswith('## '):
            teile.append(f'<h2>{inline(zeilen[0][3:].strip())}</h2>')
            zeilen = zeilen[1:]
            if not zeilen:
                continue
        if all(z.startswith('>') for z in zeilen):
            inhalt = ' '.join(z[1:].strip() for z in zeilen)
            teile.append(f'<blockquote><p>{inline(inhalt)}</p></blockquote>')
        elif all(z.startswith(('- ', '* ')) for z in zeilen):
            punkte = ''.join(f'<li>{inline(z[2:].strip())}</li>' for z in zeilen)
            teile.append(f'<ul>{punkte}</ul>')
        else:
            teile.append(f'<p>{inline(" ".join(zeilen))}</p>')
    return '\n'.join(einzug + t for t in teile)


def lesezeit(a):
    woerter = len(re.findall(r'\w+', a.vorspann + ' ' + re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', a.text)))
    minuten = max(1, round(woerter / 200))
    return '1 Minute Lesezeit' if minuten == 1 else f'{minuten} Minuten Lesezeit'


# ---------- Datum und Bild ----------

def iso(d):
    return d.strftime('%Y-%m-%dT%H:%M')


def datum_lang(d):
    return f'{d.day}. {MONATE[d.month - 1]} {d.year}, {d.hour}.{d.minute:02d} Uhr'


def datum_kurz(d):
    return d.strftime('%d.%m.%Y')


def bildgroesse(pfad):
    """Breite und Höhe aus JPEG, PNG oder WebP lesen (ohne Pakete). None, wenn unbekannt."""
    try:
        daten = pfad.read_bytes()
    except OSError:
        return None
    if daten[:8] == b'\x89PNG\r\n\x1a\n' and len(daten) >= 24:
        return struct.unpack('>II', daten[16:24])
    if daten[:2] == b'\xff\xd8':
        i = 2
        while i + 9 < len(daten):
            if daten[i] != 0xFF:
                i += 1
                continue
            marker = daten[i + 1]
            if marker == 0xFF:
                i += 1
                continue
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            laenge = struct.unpack('>H', daten[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                hoehe, breite = struct.unpack('>HH', daten[i + 5:i + 9])
                return breite, hoehe
            i += 2 + laenge
        return None
    if daten[:4] == b'RIFF' and daten[8:12] == b'WEBP' and len(daten) >= 30:
        art = daten[12:16]
        if art == b'VP8 ':
            breite, hoehe = struct.unpack('<HH', daten[26:30])
            return breite & 0x3FFF, hoehe & 0x3FFF
        if art == b'VP8L':
            b = daten[21:25]
            return 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
        if art == b'VP8X':
            return 1 + int.from_bytes(daten[24:27], 'little'), 1 + int.from_bytes(daten[27:30], 'little')
    return None


def groesse_attrs(bild):
    g = bildgroesse(PUBLIC / bild.lstrip('/'))
    return f' width="{g[0]}" height="{g[1]}"' if g else ''


def platzhalter_bild():
    return f'<div class="media-placeholder" role="img" aria-label="Platzhalter für ein Foto">{KAMERA}<span>[[Foto]]</span></div>'


def medien(a, sofort=False):
    """Bildfeld einer Karte. Das Foto wird nur zugeschnitten angezeigt, nie verzerrt."""
    if a.bild is None:
        return ''
    if a.bild == 'platzhalter':
        return f'<div class="news-card__media">{platzhalter_bild()}</div>'
    laden = ' fetchpriority="high"' if sofort else ' loading="lazy"'
    return f'<div class="news-card__media"><img src="{esc(a.bild)}" alt=""{groesse_attrs(a.bild)}{laden} decoding="async"></div>'


# ---------- Bausteine der Seiten ----------

def karte(a, art, h, rubriken, einzug, mit_rubrik=True):
    """Teaser für einen Artikel. art: lead, big, compact, wide, grid, opinion."""
    zeilen = [f'<article class="news-card news-card--{art}">']
    if art != 'opinion':
        bild = medien(a, sofort=(art == 'lead'))
        if bild:
            zeilen.append('  ' + bild)
    zeilen.append('  <div class="news-card__body">')
    if a.dachzeile:
        zeilen.append(f'    <p class="news-card__kicker">{esc(a.dachzeile)}</p>')
    zeilen.append(f'    <{h} class="news-card__title"><a class="news-card__link" href="/{a.adresse}">{esc(a.titel)}</a></{h}>')
    if art != 'compact':
        zeilen.append(f'    <p class="news-card__lede">{esc(a.vorspann)}</p>')
    if art == 'opinion':
        if a.autor:
            zeilen.append(f'    <p class="news-card__author">{esc(a.autor)}</p>')
    else:
        rubrik = f'{esc(rubriken[a.rubrik]["name"])} · ' if mit_rubrik else ''
        zeilen.append(f'    <p class="news-card__meta">{rubrik}<time datetime="{iso(a.datum)}">{datum_kurz(a.datum)}</time></p>')
    zeilen.append('  </div>')
    zeilen.append('</article>')
    return '\n'.join(einzug + z for z in zeilen)


def abschnittskopf(r, einzug, titel=None, mit_id=True, verweis=True):
    name = esc(r['name'])
    kennung = f' id="rubrik-{r["adresse"]}"' if mit_id else ''
    if titel is None:
        h2 = f'<h2{kennung}><a href="/{r["adresse"]}">{name}</a></h2>'
    else:
        h2 = f'<h2{kennung}>{esc(titel)}</h2>'
    zeilen = ['<div class="section-head">', '  ' + h2]
    if verweis:
        zeilen.append(f'  <a class="section-head__more" href="/{r["adresse"]}">Alle Artikel<span class="sr-only"> aus {name}</span> {PFEIL}</a>')
    zeilen.append('</div>')
    return '\n'.join(einzug + z for z in zeilen)


def startseite_html(artikel, rubriken, cfg):
    einstellungen = cfg.get('startseite', {})
    anzahl_neueste = int(einstellungen.get('neueste_meldungen', 6))
    je_rubrik = int(einstellungen.get('artikel_je_rubrik', 4))
    if not artikel:
        return ('\n  <section class="section">\n    <div class="container">\n'
                '      <p class="empty-note">Noch keine Artikel.</p>\n    </div>\n  </section>\n  ')
    aufmacher = next((a for a in artikel if a.aufmacher), artikel[0])
    neueste = [a for a in artikel if a is not aufmacher][:anzahl_neueste]
    teile = ['', '  <section class="top-news">', '    <div class="container top-news__grid">',
             karte(aufmacher, 'lead', 'h1', rubriken, '      ')]   # Schlagzeile des Aufmachers = Hauptüberschrift
    if neueste:
        teile += ['      <aside class="latest" aria-labelledby="neueste-meldungen">',
                  '        <h2 class="latest__title" id="neueste-meldungen">Neueste Meldungen</h2>',
                  '        <ol class="latest__list">']
        for a in neueste:
            d = a.datum
            teile.append(
                f'          <li><a class="latest__item" href="/{a.adresse}">'
                f'<time class="latest__when" datetime="{iso(d)}"><strong>{d.hour}.{d.minute:02d}</strong>{d.day:02d}.{d.month:02d}.</time>'
                f'<span class="latest__rubric">{esc(rubriken[a.rubrik]["name"])}</span>'
                f'<span class="latest__headline">{esc(a.titel)}</span></a></li>')
        teile += ['        </ol>', '      </aside>']
    teile += ['    </div>', '  </section>']

    for r in rubriken.values():
        anzahl = int(r.get('auf_startseite', je_rubrik))   # je Rubrik abweichend möglich (portal.json)
        liste = [a for a in artikel if a.rubrik == r['adresse'] and a is not aufmacher][:anzahl]
        if not liste:
            continue
        teile.append('')
        if r.get('stil') == 'meinung':
            teile += [f'  <section class="opinion-block" aria-labelledby="rubrik-{r["adresse"]}">',
                      '    <div class="container">',
                      abschnittskopf(r, '      '),
                      '      <div class="opinion-grid">']
            teile += [karte(a, 'opinion', 'h3', rubriken, '        ') for a in liste]
            teile += ['      </div>', '    </div>', '  </section>']
        else:
            teile += [f'  <section class="rubric-block" aria-labelledby="rubrik-{r["adresse"]}">',
                      '    <div class="container">',
                      abschnittskopf(r, '      '),
                      '      <div class="rubric-block__grid">',
                      karte(liste[0], 'big', 'h3', rubriken, '        ', mit_rubrik=False)]
            if len(liste) > 1:
                teile.append('        <div class="rubric-block__list">')
                teile += [karte(a, 'compact', 'h3', rubriken, '          ', mit_rubrik=False) for a in liste[1:]]
                teile.append('        </div>')
            teile += ['      </div>', '    </div>', '  </section>']
    return '\n'.join(teile) + '\n  '


def rubrikliste_html(r, liste, rubriken):
    einzug = '      '
    if not liste:
        return f'{einzug}<p class="empty-note">In dieser Rubrik gibt es noch keine Artikel.</p>'
    if r.get('stil') == 'meinung':
        teile = [f'{einzug}<div class="news-grid">']
        teile += [karte(a, 'opinion', 'h2', rubriken, einzug + '  ') for a in liste]
        teile.append(f'{einzug}</div>')
        return '\n'.join(teile)
    teile = [karte(liste[0], 'wide', 'h2', rubriken, einzug, mit_rubrik=False)]
    if len(liste) > 1:
        teile.append(f'{einzug}<div class="news-grid">')
        teile += [karte(a, 'grid', 'h2', rubriken, einzug + '  ', mit_rubrik=False) for a in liste[1:]]
        teile.append(f'{einzug}</div>')
    return '\n'.join(teile)


def mehr_html(a, artikel, rubriken):
    r = rubriken[a.rubrik]
    andere = [x for x in artikel if x.rubrik == a.rubrik and x is not a][:3]
    if not andere:
        return ''
    art = 'opinion' if r.get('stil') == 'meinung' else 'grid'
    teile = ['  <section class="section section--alt">', '    <div class="container">',
             abschnittskopf(r, '      ', titel=f'Mehr aus {r["name"]}', mit_id=False),
             '      <div class="news-grid">']
    teile += [karte(x, art, 'h3', rubriken, '        ', mit_rubrik=False) for x in andere]
    teile += ['      </div>', '    </div>', '  </section>']
    return '\n'.join(teile)


def figur_html(a):
    if a.bild is None:
        return ''
    if a.bild == 'platzhalter':
        bild = f'<div class="article__media">{platzhalter_bild()}</div>'
    else:
        bild = f'<img src="{esc(a.bild)}" alt="{esc(a.bildtext)}"{groesse_attrs(a.bild)} fetchpriority="high" decoding="async">'
    unterschrift = esc(a.bildtext)
    if a.bildnachweis:
        unterschrift += (' ' if unterschrift else '') + f'<span class="article__credit">Foto: {esc(a.bildnachweis)}</span>'
    zeilen = ['      <figure class="article__figure">', '        ' + bild]
    if unterschrift:
        zeilen.append(f'        <figcaption>{unterschrift}</figcaption>')
    zeilen.append('      </figure>')
    return '\n'.join(zeilen)


def kurzbeschreibung(a):
    text = ' '.join((a.beschreibung or a.vorspann).split())
    if len(text) <= 160:
        return text
    return text[:157].rsplit(' ', 1)[0] + ' …'


def artikelseite(a, artikel, rubriken, cfg, vorlage, teile):
    r = rubriken[a.rubrik]
    basis = f'https://{cfg["domain"]}' if cfg.get('domain') else ''
    og = ''
    if basis:
        og += f'<meta property="og:url" content="{basis}/{a.adresse}">\n'
        if a.bild and a.bild != 'platzhalter':
            og += f'<meta property="og:image" content="{basis}{esc(a.bild)}">\n'
    werte = {
        'vermerk': VERMERK.format(quelle=f'artikel/{a.datei.name}'),
        'name': esc(cfg['name']),
        'titel': esc(a.titel),
        'beschreibung': esc(kurzbeschreibung(a)),
        'og_zusatz': og,
        'rubrik_adresse': r['adresse'],
        'rubrik_name': esc(r['name']),
        'dachzeile': f'<p class="article__kicker">{esc(a.dachzeile)}</p>' if a.dachzeile else '',
        'vorspann': esc(a.vorspann),
        'autor': f'<span>Von <span class="article__author">{esc(a.autor)}</span></span>' if a.autor else '',
        'datum': f'<time datetime="{iso(a.datum)}">{datum_lang(a.datum)}</time>',
        'aktualisiert': (f'<span>Aktualisiert: <time datetime="{iso(a.aktualisiert)}">{datum_lang(a.aktualisiert)}</time></span>'
                         if a.aktualisiert else ''),
        'lesezeit': lesezeit(a),
        'figur': figur_html(a),
        'text': text_html(a.text),
        'mehr': mehr_html(a, artikel, rubriken),
    }
    seite = vorlage_fuellen(vorlage, werte)
    seite = re.sub(r'\n[ \t]*\n(?=[ \t]*<div class="article__body">)', '\n', seite)   # leere Zeile ohne Foto
    return teile_einsetzen(seite, teile, '/' + r['adresse'])


def rubrikseite(r, liste, rubriken, cfg, vorlage, teile):
    werte = {
        'vermerk': VERMERK.format(quelle='werkzeuge/portal.json'),
        'name': esc(cfg['name']),
        'rubrik_name': esc(r['name']),
        'beschreibung': esc(r['beschreibung']),
        'liste': rubrikliste_html(r, liste, rubriken),
    }
    return teile_einsetzen(vorlage_fuellen(vorlage, werte), teile, '/' + r['adresse'])


def sitemap_xml(cfg, artikel, rubriken):
    basis = f'https://{cfg["domain"]}' if cfg.get('domain') else 'https://[[DOMAIN]]'
    neuester = lambda liste: max((x.aktualisiert or x.datum) for x in liste).strftime('%Y-%m-%d') if liste else None
    eintraege = [('/', neuester(artikel))]
    for r in rubriken.values():
        eintraege.append(('/' + r['adresse'], neuester([a for a in artikel if a.rubrik == r['adresse']])))
    for a in artikel:
        eintraege.append(('/' + a.adresse, (a.aktualisiert or a.datum).strftime('%Y-%m-%d')))
    for seite in ('kontakt', 'impressum', 'datenschutz'):
        if (PUBLIC / f'{seite}.html').is_file():
            eintraege.append(('/' + seite, None))
    zeilen = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for pfad, stand in eintraege:
        zeilen.append(f'  <url><loc>{basis}{pfad}</loc>' + (f'<lastmod>{stand}</lastmod>' if stand else '') + '</url>')
    zeilen.append('</urlset>')
    return '\n'.join(zeilen) + '\n'


# ---------- Ablauf ----------

def main():
    ap = argparse.ArgumentParser(description='Seiten des Newsportals aus den Artikeln bauen')
    ap.add_argument('--pruefen', action='store_true', help='nichts schreiben, nur melden')
    args = ap.parse_args()

    try:
        cfg = json.loads(EINSTELLUNGEN.read_text(encoding='utf-8'))
        rubriken = {}
        for r in cfg['rubriken']:
            if not ADRESSE_RE.match(r['adresse']) or r['adresse'] in FESTE_SEITEN or r['adresse'] in rubriken:
                raise Fehler(f'portal.json: Rubrik „{r["adresse"]}“ ist als Adresse ungeeignet oder doppelt.')
            rubriken[r['adresse']] = r
        index_datei = PUBLIC / 'index.html'
        index_text = index_datei.read_text(encoding='utf-8')
        if not AUTO_RE.search(index_text):
            raise Fehler('index.html: Die Markierungen <!-- AUTO:startseite --> und <!-- /AUTO:startseite --> fehlen.')
        if cfg['name'] not in index_text:
            print(f'Hinweis: Der Name „{cfg["name"]}“ aus portal.json kommt in index.html nicht vor. '
                  f'Name an beiden Stellen gleich halten.')
        teile = gemeinsame_teile(index_text)
        vorlage_artikel = (VORLAGEN / 'artikel.html').read_text(encoding='utf-8')
        vorlage_rubrik = (VORLAGEN / 'rubrik.html').read_text(encoding='utf-8')

        artikel, fehler = [], []
        for datei in sorted(ARTIKEL.glob('*.txt')):
            try:
                artikel.append(artikel_lesen(datei, rubriken))
            except Fehler as e:
                fehler.append(str(e))
        if fehler:
            raise Fehler('\n'.join(fehler))
        artikel.sort(key=lambda a: (a.datum, a.adresse), reverse=True)
    except Fehler as e:
        print('FEHLER: nichts gebaut.\n' + str(e))
        sys.exit(1)

    dateien = {}
    for a in artikel:
        dateien[PUBLIC / f'{a.adresse}.html'] = artikelseite(a, artikel, rubriken, cfg, vorlage_artikel, teile)
    for r in rubriken.values():
        liste = [a for a in artikel if a.rubrik == r['adresse']]
        dateien[PUBLIC / f'{r["adresse"]}.html'] = rubrikseite(r, liste, rubriken, cfg, vorlage_rubrik, teile)
    dateien[index_datei] = AUTO_RE.sub(lambda m: m.group(1) + startseite_html(artikel, rubriken, cfg) + m.group(3).lstrip('\n').lstrip(' \t'),
                                       index_text, count=1)
    dateien[PUBLIC / 'sitemap.xml'] = sitemap_xml(cfg, artikel, rubriken)
    robots = PUBLIC / 'robots.txt'
    if robots.is_file():
        basis = f'https://{cfg["domain"]}' if cfg.get('domain') else 'https://[[DOMAIN]]'
        text = robots.read_text(encoding='utf-8')
        dateien[robots] = re.sub(r'(?im)^Sitemap:.*$', f'Sitemap: {basis}/sitemap.xml', text)

    # Seiten von Artikeln, die es nicht mehr gibt (nur solche mit Vermerk)
    veraltet = []
    for seite in sorted(PUBLIC.glob('*.html')):
        if seite in dateien:
            continue
        if VERMERK_RE.search(seite.read_text(encoding='utf-8', errors='replace')[:2000]):
            veraltet.append(seite)

    geaendert = [p for p, inhalt in dateien.items() if not p.is_file() or p.read_text(encoding='utf-8') != inhalt]
    if not args.pruefen:
        for p in geaendert:
            p.write_text(dateien[p], encoding='utf-8')
        for p in veraltet:
            p.unlink()

    tun = 'würden geändert' if args.pruefen else 'geändert'
    print(f'{len(artikel)} Artikel in {len({a.rubrik for a in artikel})} von {len(rubriken)} Rubriken.')
    print(f'{len(geaendert)} Dateien {tun}' + (':' if geaendert else '.'))
    for p in geaendert:
        print('  ' + p.relative_to(PROJEKT).as_posix())
    if veraltet:
        print(('Würde löschen' if args.pruefen else 'Gelöscht') + ' (Artikel gibt es nicht mehr):')
        for p in veraltet:
            print('  ' + p.relative_to(PROJEKT).as_posix())
    mit_platzhalter = [a.datei.name for a in artikel if '[[' in a.datei.read_text(encoding='utf-8')]
    if mit_platzhalter:
        print(f'Hinweis: {len(mit_platzhalter)} Artikel enthalten noch Platzhalter [[…]] (vor dem Veröffentlichen ersetzen oder löschen).')
    ohne_nachweis = [a.datei.name for a in artikel if a.bild and a.bild != 'platzhalter' and not a.bildnachweis]
    if ohne_nachweis:
        print('Hinweis: Foto ohne Bildnachweis in ' + ', '.join(ohne_nachweis))
    if not cfg.get('domain'):
        print('Hinweis: In werkzeuge/portal.json fehlt die Domain (sitemap.xml und robots.txt enthalten [[DOMAIN]]).')


if __name__ == '__main__':
    main()
