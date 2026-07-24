# Branch Strategy

## Trunk-Based Development

All Care Navigation services use trunk-based development with three branch types.

### `main`

- Always deployable
- Every push auto-deploys to the `dev` environment
- Protected: requires PR + 1 approval + status checks to merge

### Feature Branches

- Short-lived — open a PR to `main` as soon as the work is reviewable
- Naming: `<type>/<ticket-id>-<short-description>` — see `pull-request-standards` skill.
  For `FB-*` deployment triggers use `feat/FB-<description>`.
- Delete after merge

### Release Branches

- Cut from `main` when a release is ready to stabilize
- Deploy to `stage` for validation, then promote to `prod`
- Naming: `RB-YYYY.MM.DD-major.minor.patch`

### Hotfix Branches

- Cut from the **active `RB-*`** branch for the version being patched (not from `main`)
- Follow the same release process: stage → prod
- Naming: `RB-YYYY.MM.DD-major.minor.patch` (incremented patch, same date)
- **Back-merges are handled automatically** — see [Hotfix Cascade](#hotfix-cascade-policy) below

---

## Hotfix Cascade Policy

### The Problem

When hotfixes land on an old release branch (e.g. `RB-2026.06.01-1.0.1` through `1.0.3`),
they must reach:

1. **`main`** — so `dev` is never behind prod
2. **Any newer `RB-*`** — so the next release isn't missing critical fixes

Without automation this is easy to forget, especially under incident pressure.

### Automated Cascade (primary mechanism)

The `hotfix-cascade.yml` workflow runs on every push into any `RB-*` branch.
By default it uses the **diff** strategy, which cascades only the hotfix's own
changes — so teams never need to cherry-pick. It automatically:

1. Identifies all `RB-*` branches with a **higher semver** than the current branch, plus `main`
2. For each target, applies **only the net diff of the pushed hotfix** on top of the target
   (`git apply --3way`) on a fresh `auto-cascade/<sha>/<target>` branch
3. Opens a PR from that branch into the target

Changes already present in the target ("duplicate" changes) are dropped
automatically. If the hotfix diff conflicts, the conflicted files are committed
with `<<<<<<<` markers and the PR is opened as a **draft** with resolve
instructions — so reviewers only reconcile the small hotfix diff, never the
branches' full divergence.

PRs are labeled `hotfix-cascade` and assigned to the person who pushed the
hotfix. If the diff is empty or already present, no PR is opened (idempotent).

> **Legacy `merge` strategy** — opening a PR from the whole `RB-*` branch — is
> still available via `with: { strategy: merge }` on the reusable workflow. It
> carries the branches' full divergence and is only safe when the RB shares
> history with the target.

```
RB-2026.06.01-1.0.3 (hotfix merged)
         │
         ├──► PR: 1.0.3 diff → RB-2026.06.29-1.0.0   (next release)
         └──► PR: 1.0.3 diff → main
```

### Post-RB Verification (secondary check)

After cutting a new release branch, run this command to confirm no hotfix commits
were missed by the cascade:

```bash
# List all RB-* branches older than the new one and check for unmerged commits
CURRENT_RB="RB-2026.06.29-1.0.0"

git fetch --all --prune

# Show any RB-* branches that have commits not in the new release branch
for branch in $(git branch -r | grep 'origin/RB-' | sed 's|origin/||' | sort -V 2>/dev/null || sort -t. -k1,1n -k2,2n -k3,3n); do
  count=$(git log --oneline origin/${CURRENT_RB}..origin/${branch} 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$count" -gt 0 ]]; then
    echo "⚠️  $branch has $count commit(s) not in ${CURRENT_RB}:"
    git log --oneline origin/${CURRENT_RB}..origin/${branch}
  fi
done

# Also check main
main_count=$(git log --oneline origin/${CURRENT_RB}..origin/main 2>/dev/null | wc -l | tr -d ' ')
if [[ "$main_count" -gt 0 ]]; then
  echo "ℹ️  main has $main_count commit(s) ahead of ${CURRENT_RB} (expected for ongoing work)"
fi
```

If any hotfix branches appear in the output, open a manual merge PR before proceeding
to stage deployment.

---

## Branch Lifecycle

```
main ──────────────────────────────────────────────────────────────────────────►
       │                             │
       └─► RB-2026.06.01-1.0.0       └─► RB-2026.06.29-1.0.0
                 │                              ▲
                 ├─► RB-2026.06.01-1.0.1        │ cascade PR (auto)
                 ├─► RB-2026.06.01-1.0.2  ──────┤
                 └─► RB-2026.06.01-1.0.3  ──────┘
                           │
                           └──► main (cascade PR, auto)
```

---

## Environment Mapping

| Branch | Environment | Trigger |
|---|---|---|
| `main` | dev | Every push (auto) |
| `RB-*` | stage | Manual or tag push |
| `RB-*` (approved) | prod | Manual approval gate |

---

## Feature Flags for WIP Work

When work must land in `main` (to reach `dev`) but is not yet prod-ready:

1. Wrap behind a config flag (`false` by default)
2. Enable only in `dev` manifest / local config
3. Remove the flag when feature is production-ready

Resolve the flag through your stack's config provider (e.g. NestJS
`ConfigService`, Spring `@Value`/`Environment`) rather than reading
`process.env` / `System.getenv` directly:

```ts
// NestJS example — read via ConfigService, not process.env directly
if (this.configService.get<boolean>('FEATURE_MY_WIP')) {
  // new code path
}
```
