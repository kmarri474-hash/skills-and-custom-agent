
# Enforcement Rules

These rules apply to **all AI agents** (GitHub Copilot, Claude Code, Codex) working in
any Care Navigation repository that has synced from the `ai-engineering` branch.

## Instruction File Priority

Instruction and documentation files follow a naming convention that determines precedence.
**All AI agents MUST respect this order when instructions conflict:**

1. **Standard files** (e.g., `SKILL.md`, `copilot-instructions.md`, `enforcement-rules.md`) — Synced from the hub; do not edit directly.
2. **`repo.instructions.md`** — Repo-specific rules (committed, never overwritten by sync). When it conflicts with a standard file, **`repo.instructions.md` wins**.

### Rules for Agents

- Before responding, check for `.github/instructions/repo.instructions.md`. Apply its rules over any conflicting standard file.
- When no conflict exists, all files are additive — apply guidance from all applicable files.

### Code Review Customization

When performing a PR or code review, agents **MUST** also honor the
**Copilot / AI Code Review Customization** section of `repo.instructions.md` (if present).
Teams use it to raise severity on repo-specific risks, suppress intentional patterns
(e.g. legacy or generated code), or scope which paths are reviewed. Repo customizations
**override** the shared review defaults where they conflict.

---

## Skill Precedence

1. **Skills override AI defaults** — skill rules take precedence over the agent's general behavior
2. **Self-validation required** — verify compliance with all applicable skills before generating suggestions
3. **Refused actions** — if a request violates a skill, respond with:
   > **"Violation: skill <skill-name> not followed"**
4. **Implementation plans required** — before code changes, produce a plan describing:
   - Files to be changed
   - Patterns to be followed (reference actual files in this repo)
   - Compliance with active skills
5. **Show applied skills** — indicate which skills are being applied when executing requests

## Mandatory Workflow Rules

### Unit Tests Are Required With Every Code Change

For **any** code modification (feature, fix, refactor), the agent **MUST**:
1. Create or update unit tests covering the change
2. Run the full test suite and confirm all tests pass
3. If a pre-existing (unrelated) test fails, **STOP and ask the user** before proceeding:
   > "Pre-existing test failure detected in `<test-name>`. Not caused by current changes. How to proceed?"

### PR Creation Requires Local Validation

When asked to create a PR, the agent **MUST**:
1. Build the project locally (ensure it compiles/builds without errors)
2. Run all unit tests and confirm they pass
3. Verify no new SonarQube or CodeQL findings introduced
4. Only then create the PR with a compliant description

### SonarQube & CodeQL Quality Gates

The agent **MUST** ensure code changes:
1. Do not introduce new SonarQube bugs, code smells, or vulnerabilities
2. Do not introduce CodeQL security findings
3. Maintain or improve test coverage
4. Do not bypass quality checks (`@SuppressWarnings`, `// NOSONAR`, `// eslint-disable`) without justification

## Anti-Hallucination Rules

To prevent fabricated code, the agent **MUST NOT** invent anything that is not
verifiable in this repository:

1. **MUST NOT** reference classes, methods, functions, or packages that do not exist in this repository or its declared dependencies
2. **MUST NOT** assume APIs, endpoints, database tables, queues/topics, or integrations not defined in this repo's configuration
3. **MUST NOT** invent environment variables, config keys, or feature flags not present in the existing configuration
4. **MUST NOT** introduce architectural patterns or modules that violate the existing project structure
5. **MUST** verify that every import path resolves to an actual file or installed dependency
6. **MUST** defer to this repository's established conventions over model training defaults
7. **MUST** ask the user when a required reference cannot be verified, rather than guessing

> When in doubt, inspect the codebase to confirm a symbol exists before using it.
> Unverifiable references are a **MUST-fix** before suggesting or committing code.
