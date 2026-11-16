# So entsteht ein Artikel

Jeder Artikel ist eine einfache Textdatei in diesem Ordner. Daraus baut
`python3 werkzeuge/artikel_bauen.py` die Artikelseite, die Rubrikseite, die
Startseite und die Sitemap. Dieser Ordner wird nie hochgeladen, nur das Ergebnis
in `public/`.

## Dateiname = Adresse

`budget-2027.txt` wird zu `https://<domain>/budget-2027`. Nur Kleinbuchstaben,
Ziffern und Bindestriche, keine Umlaute (ä wird ae), kein ß, keine Leerzeichen.
Die Adresse nach dem Veröffentlichen nicht mehr ändern (Links und Google-Treffer
zeigen darauf).

## Aufbau der Datei

Oben die Angaben, je eine Zeile `Name: Wert`, dann eine Leerzeile, dann der Text.

```
Titel: Schlagzeile des Artikels
Dachzeile: Stichwort über der Schlagzeile
Rubrik: Politik
Datum: 2026-11-16 14:30
Autor: Vorname Nachname
Vorspann: Zwei bis drei Sätze, die das Wichtigste zusammenfassen.
Bild: /assets/images/artikel/budget-2027.jpg
Bildtext: Was auf dem Foto zu sehen ist.
Bildnachweis: Name der Fotografin oder Agentur
Aufmacher: ja

Erster Absatz.

Zweiter Absatz mit einem [Link](https://www.example.org) und **fettem Text**.

## Zwischentitel

> Ein wörtliches Zitat.

- Aufzählung
- Aufzählung
```

| Angabe | Pflicht | Bedeutung |
|---|---|---|
| Titel | ja | Schlagzeile |
| Rubrik | ja | Politik, Wirtschaft, Chronik, Wissen, Digital, Kultur, Sport oder Meinung (Liste in `werkzeuge/portal.json`) |
| Datum | ja | Erscheinungszeit, `2026-11-16 14:30` oder `16.11.2026 14:30`; die Reihenfolge auf der Website richtet sich danach |
| Vorspann | ja | Erscheint fett unter der Schlagzeile und auf den Teasern |
| Dachzeile | nein | Kurzes Stichwort über der Schlagzeile (bei Meinung: Kommentar, Leitartikel, Gastbeitrag, Analyse) |
| Autor | nein | Erscheint als „Von …“ |
| Aktualisiert | nein | Zeitpunkt einer späteren Änderung, wird zusätzlich angezeigt |
| Bild | nein | Foto in `public/assets/images/artikel/`, angegeben ab `/assets/images/`; `platzhalter` zeigt eine graue Fläche; leer lassen für einen Artikel ohne Foto |
| Bildtext, Bildnachweis | nein | Unter dem Foto; der Bildnachweis erscheint als „Foto: …“ |
| Beschreibung | nein | Text für Suchmaschinen, sonst der Vorspann |
| Aufmacher | nein | `ja`: Der neueste Artikel mit „ja“ steht groß oben auf der Startseite. Ohne „ja“ ist es der neueste Artikel überhaupt |

Fotos nur zuschneiden, nie bearbeiten (Regel des Auftraggebers).

## Nach jeder Änderung

1. `python3 werkzeuge/artikel_bauen.py`
2. Prüfen mit den Programmen des Skills `website-bauen` (`seiten_pruefen.py`,
   `layout_pruefen.js`), Bildschirmfotos ansehen.
3. Hochladen: `upload_paket.py` packt genau die geänderten Seiten.

Die Dateien `beispiel-*.txt` sind nur Platzhalter, damit man die Gestaltung sieht.
Sobald echte Artikel da sind, werden sie gelöscht und die Seiten neu gebaut.
