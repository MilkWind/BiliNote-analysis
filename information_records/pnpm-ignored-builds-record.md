# BiliNote Analysis — pnpm ERR_PNPM_IGNORED_BUILDS Record

*Record date: 2026-08-09*

---

## 1. The Error

While running `pnpm install` in `BillNote_frontend/`, pnpm printed the following warning (exit code 0, non-fatal):

```
[ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: core-js@3.49.0, esbuild@0.25.12

Run "pnpm approve-builds" to pick which dependencies should be allowed to run scripts.
```

### Root Cause: pnpm ≥10 blocks dependency build scripts by default

- Since pnpm v10, **all lifecycle scripts of dependencies are blocked by default** (a supply-chain security hardening change).
- Many packages rely on a `postinstall` script during installation:
  - `esbuild`: `node install.js` — validates / optimizes the platform-specific native binary.
  - `core-js`: runs a small `postinstall` probe script.
- pnpm provides an allowlist mechanism so the user can explicitly opt in:
  - **Interactive**: `pnpm approve-builds`
  - **Non-interactive**: declare the packages in the project's build-settings file.

> Note: the project's `BillNote_extension/package.json` pins `packageManager: pnpm@9.7.1` (build scripts still run by default), while the frontend has no such pin, so the global pnpm 11.20.0 was used and triggered the block.

## 2. What Happened

1. `pnpm approve-builds` was run at some point in `BillNote_frontend/`, which generated a config file (`pnpm-workspace.yaml`) with **unfinished placeholder values**:

   ```yaml
   allowBuilds:
     core-js: set this to true or false
     esbuild: set this to true or false
   ```

   The interactive selection was never completed, leaving literal placeholder text in the file.

2. Because the allowlist was malformed/incomplete, pnpm still considered `core-js` and `esbuild` as **not approved**, and every subsequent `pnpm install` re-emitted `[ERR_PNPM_IGNORED_BUILDS]`.

3. Environment: pnpm `11.20.0` (the new `allowBuilds` config schema lives in `pnpm-workspace.yaml` for pnpm 10.17+; older pnpm used `onlyBuiltDependencies` in `package.json`).

## 3. The Fix

1. Complete the placeholder values in `BillNote_frontend/pnpm-workspace.yaml`:

   ```yaml
   allowBuilds:
     core-js: true
     esbuild: true
   ```

2. Re-run the install so the approved scripts actually execute:

   ```
   pnpm install
   ```

3. Confirmed success — both postinstall scripts ran:

   ```
   esbuild@0.25.12 postinstall$ node install.js
   core-js@3.49.0  postinstall$ node -e "try{require('./postinstall')}catch(e){}"
   core-js@3.49.0 postinstall: Done
   esbuild@0.25.12 postinstall: Done
   ```

   The warning no longer appears on subsequent installs.

## 4. The Principle

### 4.1 Supply-chain security: "ignore by default, allow explicitly"

- Starting with pnpm v10, installing a package no longer implicitly trusts its build scripts. This prevents a compromised or malicious dependency from silently executing arbitrary code on the developer's machine during `pnpm install`.
- Approval is **explicit and auditable**: the list of allowed packages is stored in project config (`allowBuilds` in `pnpm-workspace.yaml`, or legacy `onlyBuiltDependencies` in `package.json`), so the trust decision is visible in version control.

### 4.2 Where the config lives depends on pnpm version

| pnpm version | Config location | Key |
|---|---|---|
| < 10 | n/a | build scripts always run |
| 10.x (early) | `package.json` | `pnpm.onlyBuiltDependencies` |
| 10.17+ / 11.x | `pnpm-workspace.yaml` | `allowBuilds: <pkg>: true\|false` |

`allowBuilds` also supports an explicit `false` — allowing a package to be permanently *excluded* even if a transitive dependency pulls it in.

### 4.3 Why these packages need their scripts

- **esbuild**: ships prebuilt platform binaries as separate optional packages; its `postinstall` validates the binary is correctly placed and warns on mismatch. Skipping it usually still works but can cause cryptic "binary not found / version mismatch" errors later.
- **core-js**: its postinstall is a benign probe; skipping has no functional impact, but approving keeps the install output clean.

### 4.4 Lesson learned

`pnpm approve-builds` writes real config entries — if the interactive session is aborted early it can leave **placeholder strings** (`set this to true or false`) in `pnpm-workspace.yaml`. Always verify the generated file contains actual boolean values, otherwise the warning keeps recurring without any user-visible config change being obvious.
