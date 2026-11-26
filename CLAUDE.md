# WikiTicks – Arbeitsregeln

## Changelog (immer)
Jede Änderung an der Website wird im selben Commit im Changelog eingetragen.
- Ort: `index.html`, Konstante `CHANGELOG` (Liste aus `[Datum, Titel, [Einträge]]`), angezeigt unter `#changelog`.
- Neue Punkte an den letzten Abschnitt anhängen, wenn er vom selben Tag und Thema ist; sonst einen neuen Abschnitt mit Datum (z. B. „26. November 2026“) und kurzem Titel anlegen.
- Kurz und verständlich formulieren (was sich für Besucher ändert), auf Deutsch, keine technischen Details.
- Reine Korrekturen kleiner Fehler können zu einem Punkt zusammengefasst werden.

## Sonst
- Antworten auf Deutsch.
- Preise nur in Euro und nur belegte Werte.
- Artikel des Tages und Uhr des Tages nie von derselben Marke.
- Datenblatt-Daten (`datenblatt.json`) nur im Uhrenvergleich und im Aufklapper der Referenztabelle verwenden.
- Bei jeder Änderung an Bildern oder Daten `IMGV` in `index.html` hochzählen (Cache).

## Referenzartikel
- Ort: `modelle.json` → `referenzen` (Felder: id, model, ref, alias, var, t, bau, s, bh/b, vh, m, ev, x, f, zeit).
- Nur für Grundreferenzen, nicht für jede Material-, Zifferblatt- oder Farbvariante. Bei Rolex ist die Datumsausführung die Grundreferenz (z. B. 126610LN, nicht 124060).
- Varianten (Edelmetall, Platin, Zifferblätter, Größen) kommen als Absatz unter »Varianten« (`vh`) in den Artikel der Grundreferenz; ihre Referenzen als `alias`, damit Bilder und Tabellen dorthin verlinken.
- Unter »Varianten« auch wichtige Ausführungen nennen, die noch nicht auf der Seite sind, mit ihrer Referenznummer, wenn sie auf der Grundreferenz basieren – nicht alle Blattfarben, nur die wichtigen.
- Jeder neue Artikel wird einzeln committet und gepusht.

## Deployment (Hostinger)
- Automatische Bereitstellung über GitHub-Push auf `claude/vigilant-darwin-l5t91c`.
- »Erneut bereitstellen« im hPanel spielt nur den zuletzt bereitgestellten Commit erneut auf, nicht den neuesten Stand. Welcher Commit live ist, steht unter »Letzte Bereitstellung → Begehen«.
