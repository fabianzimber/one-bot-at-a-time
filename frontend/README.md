# one-bot-at-a-time Frontend

Next.js `16.2.1` Frontend und oeffentliche BFF-Schicht fuer den Trenkwalder AI Assistant.

## Stack

- Next.js App Router
- React `19.2.4`
- Tailwind CSS v4
- shadcn/ui
- `botid` fuer den Schutz der oeffentlichen Write-Routen

## Aktueller Funktionsumfang

- Chat-Oberflaeche auf `/`
- Seeded-HR-Referenzansicht auf `/mock-data`
- Streaming-Antworten via `POST /api/chat/stream`
- Dokument-Upload via `POST /api/documents`
- BotID-Pruefung und serverseitiges Rate Limiting an der BFF-Grenze
- CRLF-Normalisierung im SSE-Client, damit standardkonformes Event-Framing stabil verarbeitet wird

## Wichtige Routen

### UI

- `/`
- `/mock-data`

### BFF

- `POST /api/chat`
- `POST /api/chat/stream`
- `POST /api/documents`

## Struktur

```text
app/
  api/
    chat/
    documents/
  mock-data/
components/
  chat/
  layout/
  ui/
lib/
types/
```

## Branding

Die aktuelle visuelle Quelle der Wahrheit liegt in [app/globals.css](./app/globals.css).

- Brandfarben sind als CSS-Variablen und Tailwind-v4-Tokens hinterlegt.
- `Space Grotesk` wird als Sans-/Heading-Font geladen.
- `IBM Plex Mono` wird fuer monospace UI-Elemente und Chat-nahe Inhalte geladen.
- Das UI ist derzeit light-first; `color-scheme` ist explizit auf `light` gesetzt.

## BFF- und Service-Kopplung

Das Frontend ist nicht nur UI, sondern die oeffentliche Eingangsgrenze fuer den Service-Graphen.

- `POST /api/chat` proxy't zum Chat-Orchestrator `POST /api/v1/chat`
- `POST /api/chat/stream` proxy't zum Chat-Orchestrator `GET /api/v1/chat/stream`
- `POST /api/documents` proxy't zum RAG-Service `POST /api/v1/ingest`
- `/mock-data` rendert serverseitig ueber den Chat-Orchestrator `GET /api/v1/mock-data/hr-overview`
- Interne Requests fuehren `x-internal-api-key`, `x-request-id` und optional `_vercel_share` mit

## Environment-Variablen

- `CHAT_ORCHESTRATOR_URL`
- `CHAT_ORCHESTRATOR_SHARE_TOKEN`
- `RAG_SERVICE_URL`
- `RAG_SERVICE_SHARE_TOKEN`
- `INTERNAL_API_KEY`

Fuer branch-stabile Vorschauen sollte `CHAT_ORCHESTRATOR_URL` auf den Chat-Branch-Alias zeigen und `RAG_SERVICE_URL` auf den RAG-Branch-Alias. Keine einmaligen Deployment-URLs eintragen. Wenn sich der interne Preview-Key aendert, muss `INTERNAL_API_KEY` konsistent mit Chat-, RAG- und HR-Service aktualisiert werden.

## Scripts

```bash
npm run dev
npm run build
npm run check
```

`npm run check` fuehrt TypeScript und ESLint aus.
