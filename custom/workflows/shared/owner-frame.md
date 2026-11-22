# Owner Frame (STD-FRAME-001)

Run before scoping any fix, writing a spec, or briefing an agent. Owner, 22 Nov 2026: "whenever I raise an issue using one example, you tunnel-vision on that single symptom instead of asking what whole class of failures is this an instance of?"

1. **Example → failure class.** The owner's example is one symptom. Name the class as "every X must be Y" (e.g. "every in-stock listing must be able to compete on price on 1 Dec").
2. **Sibling scan.** List every sibling failure mode in that class and pull a live count for each, with its source, before proposing any fix. A spec that names only the example is NOT READY.
3. **Commercial stakes.** State the impact in £ at risk, margin, sales velocity or deadline, never in row or SKU counts alone. Where the system cannot give the £ figure, that missing link is itself a finding.
4. **Bounded goals and non-goals.** The target, plus the guardrail that never bends (e.g. "100% in-stock coverage before 1 Dec, never below true landed cost"), plus the perfectionism it rules out (e.g. "penny-perfect accounting is a non-goal").

Worked case, 22 Nov 2026: the owner raised "the TP-Link router can't be costed". Class: every in-stock listing must be able to compete on 1 Dec. Siblings counted: 27 cost VAT unclear, 22 no measured cost, 8 router fit fee, 7 fee quote missing or stale, 6 other, out of 257 listings. Stakes: an uncompetitive listing loses the Buy Box once SellerToolKit ends on 1 Dec. Guardrail: never below true landed cost.

Relation: G-RG-10 counts the class of a defect already found; this frame applies the same at planning time, and adds stakes and goals.
