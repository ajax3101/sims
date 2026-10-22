# Frontend

The React application is served by Vite during development. Start the API on port 8000, then run:

```sh
npm ci
npm run dev
```

The development server proxies `/api` requests to `http://127.0.0.1:8000`. Set `SIMS_API` to use another API address.

Available checks:

```sh
npm test
npm run typecheck
npm run build
```
