# Kisaan Dost Web Dashboard (Next.js)

Admin / advisor / operations panels — **Phase 2** (advisor portal). The farmer
product is the Flutter app; this dashboard exists for internal users.

**Rules:** [docs/RULES.md §2.3](../docs/RULES.md) — TypeScript strict, TanStack Query
for server state, Tailwind + shadcn/ui, REST only (same `/api/v1` as the app).

## Layout

```
src/
├── app/          App Router routes (login, dashboard, farms, alerts, prices)
├── components/   UI components (shadcn/ui based)
├── lib/          API client (generated from OpenAPI), auth helpers
└── types/        shared TS types
```

## Run

```bash
npm install
npm run dev        # http://localhost:3000
```
