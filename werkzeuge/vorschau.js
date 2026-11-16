#!/usr/bin/env node
/* Vorschau einer Website auf dem eigenen Rechner. Braucht nur Node, keine Pakete.

   Aufruf:  node vorschau.js [--ordner public] [--port 4173] [--formular fehler|ok]

   Verhält sich bei den Adressen wie der spätere Server: /kontakt statt
   /kontakt.html, eigene Fehlerseite, dieselben Schutz-Einstellungen
   (Content-Security-Policy und Co. werden aus <ordner>/.htaccess gelesen, damit
   z. B. ein verbotenes Inline-Skript schon in der Vorschau auffällt).

   Nicht nachgebildet: PHP (das Formular wird NICHT versendet, es kommt eine klare
   Meldung) und eigene Weiterleitungen aus der .htaccess. Beides prüft der Skill
   website-sicherheitscheck in seiner Testumgebung mit echtem Apache und PHP. */
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

function arg(name, fallback) {
  const i = process.argv.indexOf('--' + name);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}
const ROOT = path.resolve(arg('ordner', 'public'));
const PORT = Number(arg('port', 4173));
const FORM = arg('formular', 'fehler');

if (!fs.existsSync(path.join(ROOT, 'index.html'))) {
  console.error('Keine index.html in ' + ROOT + ' gefunden. Ordner mit --ordner angeben.');
  process.exit(1);
}

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.xml': 'application/xml; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.avif': 'image/avif', '.gif': 'image/gif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.pdf': 'application/pdf', '.mp4': 'video/mp4', '.webmanifest': 'application/manifest+json'
};

// Schutz-Einstellungen aus der .htaccess übernehmen (bei jedem Aufruf neu gelesen,
// damit Änderungen sofort wirken). Zeilen mit Bedingung (expr=…, z. B. HSTS nur
// bei HTTPS) gelten in der Vorschau nicht.
function securityHeaders() {
  const headers = {};
  let text = '';
  try { text = fs.readFileSync(path.join(ROOT, '.htaccess'), 'utf8'); } catch (e) { return headers; }
  text.split(/\r?\n/).forEach((line) => {
    const m = line.match(/^\s*Header\s+always\s+set\s+([A-Za-z-]+)\s+"((?:[^"\\]|\\.)*)"\s*$/);
    if (m) headers[m[1]] = m[2].replace(/\\"/g, '"');
  });
  return headers;
}

function send(res, status, headers, body, head) {
  res.writeHead(status, Object.assign({ 'Cache-Control': 'no-store' }, securityHeaders(), headers));
  res.end(head ? undefined : body);
}
function sendFile(res, file, status, head) {
  fs.readFile(file, (err, data) => {
    if (err) return send(res, 500, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Datei nicht lesbar.', head);
    send(res, status, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' }, data, head);
  });
}
function notFound(res, head, status) {
  const page = path.join(ROOT, '404.html');
  if (fs.existsSync(page)) return sendFile(res, page, status || 404, head);
  send(res, status || 404, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Seite nicht gefunden.', head);
}
function redirect(res, to) {
  send(res, 301, { Location: to, 'Content-Type': 'text/plain; charset=utf-8' }, 'Weiter zu ' + to);
}
const isFile = (p) => { try { return fs.statSync(p).isFile(); } catch (e) { return false; } };

const server = http.createServer((req, res) => {
  const head = req.method === 'HEAD';
  const q = req.url.indexOf('?');
  const query = q === -1 ? '' : req.url.slice(q);
  let pathname;
  try { pathname = decodeURIComponent(q === -1 ? req.url : req.url.slice(0, q)); }
  catch (e) { return notFound(res, head); }

  if (/^\/api\/contact\/?$/.test(pathname) && req.method === 'POST') {
    req.resume();
    return req.on('end', () => {
      if (FORM === 'ok') return send(res, 200, { 'Content-Type': 'application/json; charset=utf-8' }, JSON.stringify({ ok: true }));
      send(res, 503, { 'Content-Type': 'application/json; charset=utf-8' },
        JSON.stringify({ error: 'Vorschau: Hier wird nichts versendet. Auf dem Server verschickt das Formular die Nachricht.' }));
    });
  }
  if (req.method !== 'GET' && !head) {
    return send(res, 405, { 'Content-Type': 'text/plain; charset=utf-8', Allow: 'GET, HEAD' }, 'Nicht erlaubt.');
  }
  // Wie auf dem Server: nichts aus /api/, keine versteckten Dateien, keine
  // Zugangsdaten oder Sicherungskopien.
  const lower = pathname.toLowerCase();
  if (pathname.includes('\0') || pathname.split('/').includes('..') || lower.startsWith('/api/') || lower.includes('.php') ||
      /(^|\/)\./.test(pathname) || /(^|\/)config[^/]*$/.test(lower) || /(~|\.(bak|old|orig|save|swp|tmp|log|md))$/.test(lower)) {
    return notFound(res, head);
  }
  // Schöne Adressen: /kontakt.html -> /kontakt, /index.html -> /, /kontakt/ -> /kontakt
  let m = pathname.match(/^\/([a-z0-9-]+)\.html$/i);
  if (m) return redirect(res, (m[1].toLowerCase() === 'index' ? '/' : '/' + m[1]) + query);
  m = pathname.match(/^\/([a-z0-9-]+)\/$/);
  if (m && isFile(path.join(ROOT, m[1] + '.html'))) return redirect(res, '/' + m[1] + query);

  let file = path.join(ROOT, pathname);
  if (!file.startsWith(ROOT)) return notFound(res, head);
  if (pathname.endsWith('/')) file = path.join(file, 'index.html');
  if (isFile(file)) return sendFile(res, file, 200, head);
  if (/^\/[a-z0-9-]+$/.test(pathname) && isFile(file + '.html')) return sendFile(res, file + '.html', 200, head);
  notFound(res, head);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') console.error('Port ' + PORT + ' ist belegt. Anderen Port mit --port wählen.');
  else console.error(err.message);
  process.exit(1);
});
server.listen(PORT, '127.0.0.1', () => {
  console.log('Vorschau läuft: http://127.0.0.1:' + PORT + '  (Ordner: ' + ROOT + ')');
  console.log('Das Formular wird in der Vorschau nicht versendet' + (FORM === 'ok' ? ' (Erfolg wird nur vorgetäuscht).' : '.'));
});
