# Test Specification — CMN-C2-680

## Test Strategy
- Coverage target: **80%+** (achieved 92%, `--cov=src`)
- Test types: Unit (pre/post + inner nodes + services) / Unit (Cat 2 graph wiring) / Integration / Proof-of-Boundary
- CI runs `pytest tests/` on the **real SDK** (`agenticstar-agentcore==1.0.0`, wheel-era — no committed local SDK stub).

## Framework Compliance Tests (Mandatory)

| TC-ID | Test | Expected Result | Result |
|-------|------|----------------|--------|
| TC-01 | State contract: flat TypedDict | `State(AgentState)`, NotRequired primitives + JSON strings; no PII | ✅ PASS |
| TC-02 | S-2 input hook never hard-rejects | `_extra_security_gate_input` is a pass-through — never raises, never `status=ERROR` (SDK 1.0.0); injection / oversize / empty handled as degraded `SUCCESS + error_code` in `execute()` (see BL-06 / BL-09) | ✅ PASS |
| TC-03 | No JWT/Credential in `src/` | `gate-credential-scan`: 0 violations | ✅ PASS |
| TC-05 | S-4: no duplicate lifecycle events | only domain events emitted | ✅ PASS |
| TC-06 | S-2 `_security_gate_input()` not overridden | `@final`; only `_extra_*` extended | ✅ PASS |
| TC-07 | S-3 `_security_gate_output()` not overridden | `@final`; may raise via `_extra_*` | ✅ PASS |
| TC-08 | `required_trust_level` enforced | VERIFIED_EXTERNAL on all FunctionNode subclasses | ✅ PASS |
| TC-11 | S-4: ≥1 domain `emit_trace_event()` per `execute()` | emitted on every path | ✅ PASS |

## Proof-of-Boundary Tests (Mandatory)

| PB-ID | Boundary | Expected Result | Result |
|-------|----------|----------------|--------|
| PB-1 | `emit_trace_event()` fires from `shared.utils.audit_logger` | No silent failures | ✅ (real SDK on CI) |
| PB-2 | Post-invoke State is primitives only | No Pydantic/dataclass | ✅ PASS |
| PB-4 | Import isolation — no Level 0 imports | AST scan: 0 violations | ✅ PASS |
| PB-6 | Invoke order S-1 → S-4 → S-2 → execute → S-3 → S-4 | Order verified | ✅ (real SDK on CI; local stub env-diff locally) |
| PB-7 | HITL interrupt propagation *(conditional)* | **Auto-waived — non-HITL** (`hitl.enabled` not set) | ✅ SKIPPED |
| Composition | Cat 2 `GraphNode`-in-main wraps inner `BaseGraph` (cached) | gate-composition passes | ✅ (S-0 gate) |

## Business Logic Tests

| BL-ID | Test | Input | Expected Result | Result |
|-------|------|-------|----------------|--------|
| BL-01 | Full design package | multi-dimension design question | ≥4 cited sections + validation checklist | ✅ PASS |
| BL-02 | Broad query covers all dimensions | "how to handle user feedback?" | all 5 dimensions present | ✅ PASS |
| BL-03 | Intent classification (specific) | "taxonomy + review routing" | focus dims = {taxonomy, review_routing} | ✅ PASS |
| BL-04 | Off-topic (out-of-scope) | non-feedback question | `out_of_scope`, no citations | ✅ PASS |
| BL-05 | Empty input | "   " | degraded SUCCESS, still audits | ✅ PASS |
| BL-06 | Injection → degraded, not ERROR | bare injection string | `SUCCESS + INJECTION_REJECTED`; body discarded (`validated_input="{}"`); node-chain reaches post_process; out-of-scope + audit; injection canary absent from output | ✅ PASS |
| BL-07 | PII / secret redaction | email / phone / token in feedback example | redacted before persistence | ✅ PASS |
| BL-08 | S-3 output gate | grounded package missing disclaimer | gate raises; unsupported section dropped; injection neutralized | ✅ PASS |
| BL-09 | Oversize → degraded, not ERROR | 20 001-char input | `SUCCESS + INPUT_TOO_LONG`; body discarded (`validated_input="{}"`); out-of-scope + audit; real `Graph().invoke()` reaches PostProcessNode; disclaimer present; no oversized canary in output | ✅ PASS |
| BL-10 | Injection-only via `Graph().invoke()` | bare injection string | reaches post_process; neutralized to out-of-scope safe answer + disclaimer/audit | ✅ PASS |

## Test Execution Summary
- Total: 55 (unit 41 [nodes 28 + graph 13] + integration 9 + PB 5 scaffold)
- unit + integration: **49 passed · 1 skipped** (server import — local stub env-diff locally; runs on real SDK in CI)
- PB (proof-of-boundary): run on the real SDK in CI (local stub env-diff locally)
- Coverage: **92%** (`--cov=src`, unit + integration)
