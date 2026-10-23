# Deviations from the submitted documents

Part-2 requires every deviation from the submitted SRS, SAD and Test Plan to be **documented and explained during the final demo**. Add a row here in the same pull request that causes the deviation (the PR template reminds you).

| ID | Document and section | What was submitted | What the product does now | Reason | PR / issue | Date | Approved by |
|---|---|---|---|---|---|---|---|
| - | - | No deviation recorded yet. At the start of Sprint 1 the code matches the Part-1 documents. | - | - | - | - | - |

## Things to watch for (common sources of deviations)

* A requirement is implemented differently, or later, than the SRS says (for example moved to a different sprint is **not** a deviation; changing its behaviour is).
* An interface in the SAD API section (function signature, exit status, message text) changes.
* A test case in the Test Plan is added, removed or its expected result changes.
* The product-ownership table says one member owns a feature but another member actually raised the PR.
* A CI check or tool used in practice differs from the Test Plan environment.

## Already documented in the Part-1 Test Plan (not deviations)

Defects D-1 to D-4 (Test Plan section 14), including the script file descriptor fix (SR-08).
