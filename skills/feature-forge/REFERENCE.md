# Feature Forge — Reference Guide

## Phase 1: Grill (Requirement Refinement)

**Invoke**: `grill-with-docs` skill

**Purpose**: Challenge the requirement until you reach shared understanding. Don't jump to code.

**Steps**:
1. Load `grill-with-docs` skill
2. Walk every branch of the decision tree with the user
3. Document decisions in `docs/CONTEXT.md` (domain terms, boundaries, constraints)
4. Create ADRs in `docs/adr/` for each architectural decision:
   - ADR format: `ADR-NNN-<slug>.md` with Status, Context, Decision, Consequences
   - Example: `ADR-001-netra-ai-3x-upgrade.md`, `ADR-002-url-routing-strategy.md`
5. If no existing CONTEXT.md/ADR folder, create them

**Gate**: User confirms shared understanding. CONTEXT.md and at least one ADR committed.

**Alternative**: If the user already has a clear spec, use `grill-me` (lighter — no doc updates) just to stress-test the plan.

---

## Phase 2: Plan (PRD + Issues)

**Invoke**: `to-prd` → `to-issues` skills (in sequence)

**Steps**:
1. Load `to-prd` — synthesize conversation context into a PRD
2. Publish PRD as a GitHub issue (parent issue)
3. Load `to-issues` — break PRD into vertical-slice implementation issues
4. Each issue should be independently grabbable (tracer-bullet slices, not horizontal layers)
5. Create all issues on GitHub with proper labels and linked to PRD parent

**Issue sizing guidance** (from this session):
- Phase 1 = core upgrade/migration (1 issue)
- Phase 2 = one issue per component group (e.g., "Table + Checkbox + Skeleton", "Card + Badge")
- Keep issues small enough to be a single PR

**Gate**: PRD issue created, child issues created, all linked.

---

## Phase 3: Explore (Codebase Discovery + Implementation Plan)

**Invoke**: `coding-standards` + `nextjs-ai` skills

**Steps**:
1. Load `coding-standards` — understand naming conventions, folder structure, hooks vs services
2. Load `nextjs-ai` — understand Next.js patterns (server vs client components, route structure)
3. Map affected files using `semantic_search`, `grep_search`, `file_search`
4. Read every file that will be modified (don't guess — read first)
5. Identify test files that need updating
6. Write implementation plan as a todo list with specific files and changes

**Key discoveries to make**:
- Which components are client vs server?
- What's the import path convention? (`@/app/_components/` vs relative)
- What mock patterns does `jest.setup.ts` use?
- What's the transform config in `jest.config.js`?
- Are there package-specific transpile requirements?

**Gate**: Implementation plan written as todo list. All affected files identified.

---

## Phase 4: Build (Implementation + Tests)

**Invoke**: `tdd` + `coding-standards` + `logging` skills

**Steps**:
1. Load `tdd` — follow red-green-refactor for each change
2. Load `logging` — use shared logger, never `console.log`
3. Load `coding-standards` — follow naming, structure, `'use client'` rules
4. Work through issues one at a time, mark each in-progress → completed
5. For each component change:
   a. Update the component file
   b. Add/update mock in `jest.setup.ts` if it's a new UI primitive
   c. Update the test file
   d. Run the specific test: `npx jest --no-coverage <test-file>`
   e. Fix until green
6. After all component changes, run full test suite: `npx jest --no-coverage`

**Jest Mock Patterns** (critical lessons):

```typescript
// In jest.setup.ts — mock a passthrough component
jest.mock('@uhg-netra-ai/core-react-components/ui/tabs', () => {
  const R = require('react');
  const mockPassthrough = (name: string) =>
    ({ children, ...props }: any) => R.createElement('div', { 'data-testid': `netra-${name}`, ...props }, children);
  return {
    __esModule: true,
    Tabs: mockPassthrough('tabs'),
    TabsList: mockPassthrough('tabs-list'),
    TabsTrigger: mockPassthrough('tabs-trigger'),
  };
});

// Mock native HTML element (checkbox)
jest.mock('@uhg-netra-ai/core-react-components/ui/checkbox', () => ({
  __esModule: true,
  Checkbox: (props: any) => require('react').createElement('input', { type: 'checkbox', ...props }),
}));
```

**Rules**:
- `jest.mock()` factories run in a hoisted scope — cannot reference `React` from imports
- Use `require('react')` inside the factory
- Helper functions inside factories must be prefixed with `mock` (Jest convention)
- Add new packages to `transformIgnorePatterns` in `jest.config.js` if they ship ESM

**Gate**: Full test suite passes (all suites, all tests). Zero failures.

---

## Phase 5: Heal (Debug Runtime Issues)

**Invoke**: `diagnose` skill

**Purpose**: The app may compile tests fine but fail at runtime. This phase catches that.

**Steps**:
1. Start the dev server: `npm run dev` (or the app-specific command)
2. Test every route with curl:
   ```bash
   curl -s -o /dev/null -w "/ => %{http_code}\n" http://localhost:3000
   curl -s -o /dev/null -w "/forecast => %{http_code}\n" http://localhost:3000/forecast
   ```
3. If any route returns 500, check terminal output for the error
4. Load `diagnose` skill — follow: Reproduce → Minimize → Hypothesize → Instrument → Fix → Regression-test

**Common Runtime Failures**:

| Error | Cause | Fix |
|-------|-------|-----|
| `_interop_require_default._ is not a function` | `babel.config.json` at root disables SWC | Delete babel.config.json, put config inline in jest.config.js |
| `Cannot use import statement outside a module` | ESM package not transpiled by Jest | Add to `transformIgnorePatterns` exclusion list |
| Merge conflict markers in source | Stale files from unresolved merge | Clean the file, `rm -rf .next`, restart |
| `usePathname` / `useRouter` errors | Missing `'use client'` directive | Add `'use client'` at top of component file |
| Font utility classes not working | Tailwind v4 missing `@theme` vars | Add `@theme inline` block in `globals.css` |

**Gate**: All routes return HTTP 200. No console errors in server output.

---

## Phase 6: Verify (Full End-to-End Check)

**Invoke**: `run-turbo-local` skill (if in turborepo), otherwise manual verification

**Steps**:
1. Clear all caches: `npx jest --clearCache && rm -rf .next`
2. Run full test suite: `npx jest --no-coverage` — must show all suites pass
3. Start dev server fresh: `rm -rf .next && npm run dev`
4. Curl all routes — all must return 200
5. Open in browser if UI changes are involved — visual spot check

**Gate**: Tests green + app loads + routes verified. Ready to ship.

---

## Phase 7: Ship (Branch, Commit, PR, Close Issues)

**Invoke**: `pull-request` skill (MANDATORY)

**Steps**:
1. Load `pull-request` skill
2. Check current branch: `git branch --show-current`
3. If on a protected branch (`main`, `FB*`, `RB*`), create a working branch first
4. Stage changes: `git add <specific files>` (not `git add .` — exclude unrelated files)
5. Commit with temp file pattern:
   ```bash
   # Create temp file with commit message
   # git commit -F tmp-commit-msg.txt && rm tmp-commit-msg.txt
   ```
6. Push branch: `git push origin <branch-name>`
7. Create PR with full template (ALL sections required):
   ```bash
   # Create tmp-pr-body.md with full PR template
   # gh pr create --base <target> --head <branch> --title "..." --body-file tmp-pr-body.md && rm tmp-pr-body.md
   ```
8. Close completed GitHub issues:
   ```bash
   gh issue close <number> -c "Implemented and verified — all tests pass, app loads correctly."
   ```
9. If merging through intermediate branches (e.g., feature → FB → redesign → main):
   - Create PRs at each level
   - Check for merge conflicts: `gh pr view <number> --json mergeable`
   - Resolve conflicts locally if needed: `git merge origin/<target> --no-commit`, fix, commit, push

**PR Template Sections** (all REQUIRED):
- Description (detailed, not "fixed bug")
- Motivation and Context
- How Has This Been Tested?
- Tests (check one: added tests / N/A with reason)
- E2E Tests (check one: created E2E PR / N/A with reason)
- Type of Change (bug fix / new feature / breaking / tech debt / docs)
- Checklist (all must be checked)
- Related Issues (Closes #N)

**Merge Conflict Resolution**:
```bash
git fetch origin <target-branch>
git merge origin/<target-branch> --no-commit
# If conflicts: resolve each file, then:
git add <resolved-files>
git commit -F tmp-commit-msg.txt && rm tmp-commit-msg.txt
git push origin <branch>
# Verify: gh pr view <number> --json mergeable
```

**Gate**: PR created with complete template. All issues closed. PR is mergeable (no conflicts).

---

## Skill Dependency Map

```
feature-forge (orchestrator)
├── Phase 1: grill-with-docs  (or grill-me for lighter grilling)
├── Phase 2: to-prd → to-issues
├── Phase 3: coding-standards + nextjs-ai
├── Phase 4: tdd + coding-standards + logging
├── Phase 5: diagnose
├── Phase 6: run-turbo-local
└── Phase 7: pull-request
```

## Anti-Patterns (Lessons Learned)

1. **Don't skip Phase 5 (Heal)** — tests passing ≠ app working. Always start the dev server.
2. **Don't batch-commit** — commit per logical change, not one giant commit at the end.
3. **Don't create config files without checking impact** — `babel.config.json` broke the entire app because Next.js auto-detects it.
4. **Don't resolve conflicts with `--ours`/`--theirs` blindly** — read both sides, understand which version is more evolved.
5. **Don't close issues before verification** — close only after Phase 6 passes.
6. **Don't skip `rm -rf .next`** — stale caches produce phantom errors that waste hours.
7. **Don't use `git add .`** — stage specific files to avoid committing unrelated changes like `prm-repo.yaml`.
