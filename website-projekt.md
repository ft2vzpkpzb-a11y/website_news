# Projektakte: Newsportal (Arbeitstitel „Der Überblick“)

Diese Datei ist das Gedächtnis des Projekts. Claude liest sie zu Beginn jeder
Sitzung und trägt Entscheidungen sofort ein, damit auch eine neue Sitzung weiß,
was gilt. Nichts aus dieser Datei wird hochgeladen. Keine Passwörter eintragen.

## Worum es geht

- Auftraggeber: (noch nicht festgehalten)
- Zweck der Website: Nachrichtenportal („News“), orientiert an klassischen Nachrichtenseiten
- Wer soll angesprochen werden: Leserinnen und Leser in Österreich (Vorschlag von Claude, Unterzeile „Nachrichten aus Österreich und der Welt“, noch zu bestätigen)
- Name: Arbeitstitel „Der Überblick“ (Vorschlag von Claude, Entscheidung offen). Steht in `public/index.html` (Kopfzeile, Fußzeile), `werkzeuge/portal.json` und in den Seitentiteln von Kontakt, Impressum, Datenschutz, 404.
- Adresse (Domain): offen (danach in `werkzeuge/portal.json` eintragen, dann `artikel_bauen.py`)
- Vorbild für den Stil: klassische Nachrichtenseiten (Wunsch des Auftraggebers)

## Seiten

| Seite | Adresse | Datei | Stand |
|---|---|---|---|
| Startseite | / | public/index.html (Bereich AUTO:startseite wird erzeugt) | Entwurf mit Beispielartikeln |
| Rubriken (8) | /politik, /wirtschaft, /chronik, /wissen, /digital, /kultur, /sport, /meinung | public/<rubrik>.html (erzeugt) | Entwurf |
| Artikel | /<dateiname> | public/<dateiname>.html (erzeugt aus artikel/*.txt) | nur Beispiele mit Platzhaltern |
| Kontakt (Redaktion) | /kontakt | public/kontakt.html | Kontaktdaten fehlen |
| Impressum | /impressum | public/impressum.html | Text fehlt |
| Datenschutzerklärung | /datenschutz | public/datenschutz.html | Text fehlt |
| Fehlerseite | (404) | public/404.html | fertig |

## Entscheidungen des Auftraggebers

Neueste zuerst, mit Datum. Wünsche möglichst wörtlich festhalten.

- 2026-11-16: Name: „Später, mit der Domain“. Der Arbeitstitel „Der Überblick“ bleibt stehen, bis die Internetadresse feststeht; erst dann wird der Name entschieden.
- 2026-11-16: Akzentfarbe: „A: Rot“ (#B3121E). Gezeigt wurde daneben Variante B Dunkelblau (#17406D); nicht gewählt.
- 2026-11-16: Rubriken: „Nein, die acht passen“. Es bleibt bei Politik, Wirtschaft, Chronik, Wissen, Digital, Kultur, Sport, Meinung. Angeboten und nicht gewählt: Recht, Gesundheit (eigene Rubrik), Leben.
- 2026-11-16: Rubriken: „Logisch ist, dass Wirtschaft ein Teil drin sein soll und Politik. Ja, den Rest lasse ich mal dir zur Verfügung.“ Claude hat dazu vorgeschlagen: Chronik, Wissen, Digital, Kultur, Sport, Meinung.
- 2026-11-16: „Baue mir eine Website … auf der Website soll es um News gehen. Orientiere dich gerne an klassischen News-Websites.“ Gebaut mit dem Skill website-bauen.

## Vorschläge von Claude, die noch bestätigt werden müssen

- Name „Der Überblick“ und Unterzeile „Nachrichten aus Österreich und der Welt“ (Arbeitstitel, Entscheidung zusammen mit der Domain)
- Beschreibungen der Rubriken (Wortlaut von Claude, stehen in `werkzeuge/portal.json`)
- Themen im Kontaktformular: Hinweis an die Redaktion, Leserbrief, Korrektur, Sonstiges (gleich in `public/api/contact.php`, ALLOWED_TOPICS)
- Aufbau der Startseite: Aufmacher mit „Neueste Meldungen“ daneben, dann je Rubrik ein großer Artikel und eine Liste, Meinung als graue Fläche am Ende

## Aufbau und Technik (für spätere Sitzungen)

- Artikel sind Textdateien in `artikel/` (Anleitung: `artikel/ANLEITUNG.md`). `python3 werkzeuge/artikel_bauen.py` erzeugt daraus Artikelseiten, Rubrikseiten, den Bereich `AUTO:startseite` in `index.html` und `sitemap.xml`; Kopfzeile, Fußzeile und Cookie-Fenster kommen aus `index.html`. Erzeugte Seiten tragen einen Vermerk und werden gelöscht, wenn ihr Artikel gelöscht wird.
- Reihenfolge nach Änderungen: gemeinsame Teile in `index.html` → `seiten_abgleichen.py` (bei CSS oder JS mit `--version`) → `artikel_bauen.py` → `seiten_pruefen.py` und `layout_pruefen.js`.
- Alle Seiten liegen direkt in `public/` (Adressen ohne Unterordner), damit die Regeln für schöne Adressen in der `.htaccess` unverändert bleiben.
- Kopfzeile: oben der Zeitungskopf mit Datum (kommt aus `main.js`), darunter die Rubrikenleiste. Am Computer gleitet der Zeitungskopf beim Scrollen weg, die Leiste bleibt mit kleinem Namen stehen. Am Handy: Name und Menüknopf.
- Die Hauptüberschrift (h1) der Startseite ist die Schlagzeile des Aufmachers.
- Schriften: Playfair Display (Überschriften) und Inter liegen im Projekt; Artikeltext in Georgia (auf den Geräten vorhanden, lädt nichts nach).
- Beispielartikel `artikel/beispiel-*.txt` enthalten nur Platzhalter `[[…]]` (keine erfundenen Meldungen). Vor dem Veröffentlichen löschen und neu bauen.

## Texte und Bilder

- Texte: Formulierungen des Auftraggebers wörtlich übernehmen, nichts erfinden.
- Erlaubte Wörter mit Bindestrich: E-Mail
- Offen: Gilt die Regel „keine Striche“ auch für Artikeltexte? In Nachrichten sind Wörter wie „EU-Kommission“ üblich. Bis zur Entscheidung meldet `seiten_pruefen.py` Striche in Artikeln als Hinweis.
- Fotos: nur zuschneiden, nie bearbeiten. Herkunft und Rechte: je Artikel im Bildnachweis („Foto: …“). Offen: Dürfen sehr große Fotos mit weniger Bildpunkten gespeichert werden?
- Bewertungen: keine (Newsportal)

## Dienste von Dritten

Jeder Dienst lädt erst nach Zustimmung und hat einen eigenen Schalter im Cookie-Fenster.

| Dienst | Zweck | Schalter im Cookie-Fenster | Absatz in der Datenschutzerklärung | Adressen in der .htaccess |
|---|---|---|---|---|
| (keiner) | | | | |

- 2026-11-16: Google Maps aus dem Startpaket entfernt (Kontaktseite ohne Karte, Schalter entfernt, `frame-src` aus der `.htaccess` entfernt). Die Website lädt nichts von fremden Servern.
- Das Cookie-Fenster bleibt mit unverändertem Wortlaut aus dem Startpaket (Technik für spätere Dienste wie Videos, Statistik, Werbung). Ob es ohne Dienste gezeigt werden soll und welcher Wortlaut gilt, entscheidet der Auftraggeber.

## Hosting und Veröffentlichung

- Anbieter: offen
- Zielordner auf dem Server: httpdocs
- HTTPS im Kundenbereich eingeschaltet: offen
- PHP-Version auf dem Server: offen
- Zugangsdatei `config.php`: liegt nur auf dem Server im Ordner `api`
- Zuletzt hochgeladener Stand: noch nichts
- Frühere Adressen, die weitergeleitet werden: keine

## Offene Punkte

- [ ] Name des Portals und Unterzeile (Arbeitstitel „Der Überblick“), zusammen mit der Domain
- [x] Akzentfarbe: Rot (entschieden 2026-11-16)
- [x] Rubriken: die acht bleiben (entschieden 2026-11-16)
- [ ] Domain und Hosting
- [ ] Texte für Impressum und Datenschutzerklärung vom Auftraggeber
- [ ] Kontaktdaten der Redaktion (Adresse, Telefon, E-Mail) und Empfängeradresse des Formulars
- [ ] Echte Artikel und Fotos; Beispielartikel löschen
- [ ] Striche in Artikeltexten: Regel gilt oder nicht
- [ ] Cookie-Fenster ohne Dienste: behalten oder nicht, Wortlaut
- [ ] Sicherheitscheck (Skill website-sicherheitscheck) vor dem ersten Veröffentlichen
- [ ] Platzhalter `[[…]]` in allen Seiten ersetzen (`seiten_pruefen.py` findet sie)
