# Hinweise für Claude

Dieses Projekt ist die Website eines Auftraggebers ohne technische Vorkenntnisse.

1. Zuerst `website-projekt.md` lesen. Das ist die Projektakte: Zweck, Seiten,
   Entscheidungen des Auftraggebers, Hosting, zuletzt hochgeladener Stand, offene
   Punkte. Jede neue Entscheidung sofort dort eintragen, damit andere Sitzungen
   denselben Stand haben.
2. Für alle Arbeiten an der Website den Skill `website-bauen` verwenden. Vor dem
   Veröffentlichen und nach größeren Änderungen den Skill `website-sicherheitscheck`.
3. Hochgeladen wird nur der Inhalt von `public/`. Zugangsdaten
   (`public/api/config.php`, `.env`) gehören nie ins Projekt und nie in den Chat.
4. Das ist ein Newsportal. Artikel sind Textdateien in `artikel/` (Aufbau in
   `artikel/ANLEITUNG.md`). Artikelseiten, Rubrikseiten, der Bereich
   `AUTO:startseite` in `index.html` und `sitemap.xml` entstehen mit
   `python3 werkzeuge/artikel_bauen.py`; diese Dateien nie von Hand ändern.
   Reihenfolge nach Änderungen: gemeinsame Teile nur in `public/index.html`,
   dann `seiten_abgleichen.py` (bei CSS oder JS mit `--version`), dann
   `artikel_bauen.py`, dann prüfen (`seiten_pruefen.py`, `layout_pruefen.js`).
