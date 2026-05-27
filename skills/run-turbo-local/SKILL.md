---
name: run-turbo-local
description: 'Run any app in the Care Navigation turborepo locally. USE FOR: starting a dev server, checking which port an app uses, fixing NODE_OPTIONS header errors, choosing the right npm dev command, running tests for a specific app, cleaning and reinstalling node_modules, diagnosing install failures. Trigger phrases: "run locally", "start dev", "dev server", "which port", "npm run dev", "header size error", "reset install", "run tests for app".'
argument-hint: '<app-name> (e.g. ix, transition-management, care-plan-cds)'
---

# Run Care Navigation Turbo Repo Locally

## Prerequisites

Always verify Node 20 is active first:
```bash
nvm use 20
node -v   # must be v20.x.x
```

## App Dev Commands

Run from the **repo root**. These scripts include the correct `NODE_OPTIONS` flags:

| App | Command | Port |
|-----|---------|------|
| ix | `npm run dev:ix` | 3001 |
| transition-management | `npm run dev:transition-management` | 3002 |
| user-dashboard | `npm run dev:dashboard` | 3003 |
| assessment-conductor | `npm run dev:assessment-conductor` | 3004 |
| care-plan-cds | `npm run dev:care-plan-cds` | 3006 |
| sdoh | `npm run dev:sdoh` | 3008 |
| assessment-builder | `npm run dev:assessment-builer` | — |
| program-referral | `npm run dev:program-referral` | — |
| program-builder | `npm run dev:program-builder` | — |
| care-plan-builder | `npm run dev:care-plan-builder` | — |
| firefly | `npm run dev:firefly` | — |
| vep | `npm run dev:vep` | — |

> **Never** run `next dev` directly — always use the root-level `npm run dev:<app>` scripts.

For apps not in the table above, look up the app's `name` field:
```bash
cat apps/<folder>/package.json | grep '"name"'
```
Then run:
```bash
npx turbo run dev --filter=<app-name>
```

## Running Tests

```bash
# Single app
npx turbo run test --filter=<app-name>

# Common package
npm test

# Named shortcuts
npm run test:firefly
npm run test:program-builder
npm run test:care-plan-cds
npm run test:tm
```

## Installation Procedure

When `node_modules` is missing or install is broken, run in order from repo root:

```bash
# 1. Clean
rm -rf node_modules package-lock.json

# 2. Install
npm i

# 3. Validate CI compatibility
npm ci --dry-run
```

Shortcut: `npm run reset-install`

If step 2/3 fails with version conflicts, add to `package.json` → `overrides`:
```json
"overrides": {
  "<conflicting-package>": "^<required-version>"
}
```
Then repeat from step 1.

## HTTP Header Size Errors

If you see `ERR_HTTP_HEADERS_SENT` or similar header errors, the app needs `NODE_OPTIONS='--max-http-header-size=...'`. The named `dev:<app>` scripts already set this — use those, not raw turbo commands.

Current values from `package.json`:
- `ix`, `assessment-builder`, `care-plan-cds`, `vep`: `12800000`
- `transition-management`, `user-dashboard`, `program-referral`: `256000000`

## Decision Flow

```
User wants to run <app>?
  → Is there a named npm run dev:<app> script?
      YES → Use it (handles NODE_OPTIONS automatically)
      NO  → npx turbo run dev --filter=<app-name>
              (find <app-name> from apps/<folder>/package.json)
```

## Quick Diagnosis Checklist

1. `node -v` → must be v20.x.x
2. `ls node_modules` → must exist (if not, run reset-install)
3. Run correct `npm run dev:<app>` from repo root
4. Check terminal for port number in output
