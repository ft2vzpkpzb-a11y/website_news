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
