# one-bot-at-a-time Frontend

Next.js `16.2.1` Frontend fuer den Trenkwalder AI Assistant, aufgebaut mit:

- App Router
- Tailwind CSS v4
- shadcn/ui
- Brand-Tokens aus `../one-bot-at-a-time-colors.txt`

## Scripts

```bash
npm run dev
npm run build
npm run check
```

`npm run check` fuehrt TypeScript und ESLint aus.

## Struktur

```text
app/
components/
  chat/
  documents/
  layout/
  ui/
hooks/
lib/
types/
```

## Branding

Die zentrale Theme-Definition liegt in [app/globals.css](/Users/Fabia/Documents/shiftbloom/git/one-bot-at-a-time/frontend/app/globals.css).

- Brandfarben sind als CSS-Variablen und Tailwind Theme-Tokens hinterlegt.
- shadcn/ui nutzt dieselben semantischen Tokens fuer `background`, `primary`, `border`, `ring` und weitere UI-Flaechen.
- Dark Mode ist standardmaessig aktiv, damit die Seite direkt dem Brandbook folgt.

## Aktueller Stand

Die Startseite ist bewusst als minimalistische Work-in-Progress-Landing aufgebaut. Sie dient als visuelle und technische Basis fuer die naechsten Schritte:

- Chat-Oberflaeche
- Streaming-Antworten
- Tool-Zustaende
- Dokumenten-Upload
