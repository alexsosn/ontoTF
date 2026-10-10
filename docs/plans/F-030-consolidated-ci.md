# F-030 CI consolidation research-plan-TDD implementation gate

1. **Research:** enumerate every `.github/workflows/*.yml` and parse actual triggers, job steps and uniquely executed commands. Produce `workflow-ownership-v1.json`, document what the full suite already covers and what requires additional check classes. Disallow unowned legacy steps.
2. **Plan:** define stable required job names and exact-head protection. Verify current GitHub branch protection/current required status contexts before any deletion; without this, do not remove potentially required workflows.
3. **TDD RED:** add tests that mutate the inventory, omit a unique source checkout/generator, change a path trigger, or skip final-head Python 3.10/3.12. They must fail before code exists.
4. **GREEN:** one canonical PR workflow, a shared offline check runner for generated snapshots and evidence rules, and a source-pins conditional runner. Migrate groups of workflows only when inventory ownership is complete and reviewable.
5. **Measure:** for before-and-after representative changes (single mapping ledger and `src/tfont/**` infrastructure edit) record workflow count, executed tests, retries, runner-minutes and wall-clock CI. Target ordinary mapping PR 3–5 required jobs instead of ~26.
6. **Review:** logically independent adversarial review of missing test classes and malicious skip/PR event handling; verify exact-head full CI. Do not merge with broken/unknown branch protection.
7. **Release:** merge with expected SHA only after all migrated unique checks have demonstrated green parity. Keep an archive inventory rather than silently deleting history.

This is a **single F-030 architecture ticket / PR**, not a new ticket/workflow per old ticket.
