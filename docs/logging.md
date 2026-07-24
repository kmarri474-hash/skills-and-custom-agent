# Logging Standards

Structured logging standard for all Care Navigation services.
All logs are written to stdout as JSON and ingested by Dynatrace and Splunk.

---

## Log Format

This is the **normalized** log schema. Each stack maps its own logger output
to these fields — field names may differ in your implementation (e.g. a
service may emit `service` instead of `topic`); see your stack's
`logging-standards` skill for the concrete mapping. What must hold everywhere
is that each normalized concept below is present and PII/PHI-safe.

| Normalized field | Required | Description |
|---|---|---|
| `level` | ✅ | `info`, `warn`, `error`, `critical` |
| `topic` | ✅ | Service/app name (e.g. `practicemgr-nestjs-functions`) |
| `timestamp` | ✅ | ISO 8601 |
| `data.message` | ✅ | Human-readable description |
| `data.functionName` | ✅ | Class/function where the log originated |
| `data.stack` | error/critical | Error stack trace — truncate to 1,000 chars |
| `httpStatus` | API errors | HTTP status code string (`"500"`) |
| `data.requestContext` | recommended | Non-PII/PHI identifiers (`memberId`, `transactionId`) |
| `data.user.msid` | after auth | User MSID from JWT claim |

---

## Stack-Specific Setup

The concrete logger, required fields, and quick-reference snippets for **your**
stack live in the `logging-standards` skill that onboarding installed into this
repo:

- **Skill (enforced):** `.github/skills/logging-standards/SKILL.md`

That skill is the single source of truth for the logger API, the required log
fields, and the `try/catch` patterns specific to this repo's stack. This document
only covers the universal format and anti-patterns that apply to every service.

> This file is intentionally stack-agnostic. It is the same in every repo, so it
> never references other stacks' setups, PRs, or guides. For anything
> stack-specific, defer to the `logging-standards` skill above.

---

## Anti-Patterns (All Stacks)

| Anti-pattern | Fix |
|---|---|
| Empty catch block | Always log `error.message` and `error.stack` |
| Logging PII/PHI | Log IDs only (`memberId`, `transactionId`) — never names, DOB, SSN |
| `console.log` (JS) / `System.out.println` (Java) directly | Use the structured logger |
| Logging the full stack in `message` field | Pass stack as the dedicated `stack` parameter |
| Stack traces over 1,000 chars | Avoid truncating manually — pass the exception as the last SLF4J arg (`log.error("msg", e)`) and configure depth in `logback-spring.xml` via `<maxDepth>`; JS: `error.stack?.slice(0, 1000)` |
