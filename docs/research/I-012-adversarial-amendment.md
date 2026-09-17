# I-012 adversarial research amendment

This amendment records two blockers found by a logically separate challenge of the first I-012 research draft. It is normative for the later plan and supersedes any narrower wording in `I-012-clean-install-acceptance.md`.

## A. Do not let the wheel define its own acceptance oracle

The first draft suggested taking production parent/component identities from the installed bundle/compiled IR wherever practical. That is unsafe for release acceptance: an accidentally changed but internally self-consistent wheel could provide both the value under test and its expected value.

The revised research now freezes the independently reviewed I-009 parent, component, mapping-semantic and projection-semantic digests plus OLiA revision/Noun identity as acceptance constants. The loaded contexts use the frozen parent/component identities; the installed wheel is independently compared against them. Updating those constants is a reviewed release decision, not an automatic adaptation to package contents.

## B. The loaded API double must exercise prerequisite observation as well as execution

The first draft listed only the executor selector surface (`Fall`, `F.sp.s`, `F.otype.v`). That is incomplete. `execute_exact_semantic()` first builds a `LoadedTFObservation` and I-007 evaluates the production `native-value-present` dependencies. For the current three profiles that observation path requires:

- `Fall()` to prove `sp` is already loaded;
- `F.otype.s("word")` to enumerate the relevant node type;
- `F.sp.v(node)` to observe the complete native value set used by I-007;
- `F.sp.s(value)` for actual scalar/set execution after authorization;
- `F.otype.v(node)` for result node-type filtering.

The acceptance double must implement all of these. It should also expose a load/autoload sentinel that fails or increments a counter if touched, even though TFont should never invoke it.

The negative parent-drift case must assert that all **execution selector** counters (`F.sp.s`) remain zero across all requested corpora. Observation calls (`F.otype.s` / `F.sp.v`) are expected because fresh prerequisite evaluation necessarily precedes resolution; they are not native result execution.

## Review consequence

With these two amendments, I-012 remains an acceptance-only integration ticket: no new `src/tfont` surface is justified. The plan should freeze an outside-checkout fresh-venv runner that imports only installed `tfont`, independently checks the reviewed release identities, exercises both I-007 observation and I-008/I-010 native execution, asserts the existing provenance envelope, and proves parent drift blocks native result selection.
