# WikiTicks

Das Uhrenlexikon: Uhrwerke, Komplikationen, Marken und Modelle, Geschichte und Praxiswissen.

- `index.html` – die Seite (HTML, CSS, JavaScript)
- `lexikon.json` – Lexikonartikel
- `modelle.json` – Marken und Uhrenmodelle

Lokal starten (die JSON-Dateien werden per `fetch` geladen, daher einen Webserver nutzen):

```bash
python3 -m http.server 8000
```

Dann http://localhost:8000 öffnen. Für GitHub Pages: Settings → Pages → Branch wählen, Ordner `/ (root)`.
