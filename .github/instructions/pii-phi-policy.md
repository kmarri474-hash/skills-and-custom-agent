
# PII/PHI Policy

This is a **Care Navigation (healthcare)** application. All AI agents working in this
repository MUST follow these rules without exception.

## NEVER Generate Code That

- Logs PII/PHI (SSN, DOB, clinical data, diagnosis codes, member names)
- Hardcodes credentials, secrets, or API keys
- Exposes member data in error responses or log output
- Bypasses authentication or authorization controls
- Stores unencrypted sensitive data at rest
- Transmits PII/PHI over unencrypted channels

## Safe Identifiers for Logging

These may be logged because they are non-PII/PHI identifiers:
- `memberId` (opaque ID, not SSN)
- `transactionId` / `correlationId`
- `msid` (employee MSID)
- `programId`, `taskId`, `referralId`

## Logging Rule

```
# NEVER log these:
❌ member name, DOB, SSN, address, phone, email, diagnosis, clinical notes

# SAFE to log:
✅ memberId, transactionId, correlationId, msid, error.message, error.stack
```

## Error Response Rule

Never leak internal details in API responses:
```
❌ { "error": "NullPointerException at UserService.java:42", "memberId": "...", "data": {...} }
✅ { "error": "Internal server error", "statusCode": 500 }
```
