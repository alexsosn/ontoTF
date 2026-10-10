# I-033A — data-first compiler parity, bounded POS pilot

Parent #290 (architecture rework #292), Workstream C #264.

## Investigated source-backed release data

Production v0.3.0 BHSA, Syriac and ExtraBiblical each contains a 3.5KB source-reviewed Mapping v2 for `word.sp=verb -> olia:Verb`, with identical structural fields and separately pinned native evidence. The actual released BHSA coverage successor additionally has **27** individually reviewed `vs` native-only dispositions, no shared ontology targets. A single version increment required cloning noun/morphology/parent resources and whole corpus coverage manifests.

The production runtime already implements validated Mapping v2, canonical RFC8785 hashes, corpus-native dependency checks and bidirectional IR. Changing that runtime now is unnecessary. The high-leverage change is to introduce compact decision inputs and compare generated semantic output against **already independently reviewed immutable source mappings** before moving any new authority.

## Phase-1 pilot boundary

Represent three reviewed positive `olia:Verb` mappings and the 27 native-only BHSA verbal-stem rows as a compact JSON decision ledger. A deterministic Python compiler uses stable shared POS projection defaults, constructs complete mapping/projection *semantic* fields, calculates canonical V2/V1 digests itself, and then imports only excluded audit/review fields from the historical reviewed mapping on a strict digest-and-value match. Compare compiled records with the existing Mapping v2 records field-by-field; require exact corresponding coverage review accounting.

**Important:** the published mapping file is an approval anchor for parity only. This phase **does not** authorize new mappings or accept user-declared `reviewed:true` as a replacement for independent review authority. A later phase must specify externally verified review receipts before the compiler may publish previously unreviewed rows.

The builder must reject changed source pin, forged target, altered native selector, modified evidence digest, missing published mapping, or altered native-only source IDs. The historical mapping files and complete coverage successors remain byte-identical; pilot output is only a compact inspection report, not a fresh release.

## Why this is not enough yet

The remaining bottlenecks are the immutable-pack writer, independently authenticated batch review receipts, generic profile loader and consolidated CI. They remain explicit acceptance criteria in #290/#291. Never claim phase-1 parity itself is the complete new release architecture.

## Acceptance

≥30 actual corpus-native reviewed decisions represented by one compact ledger; 3 published Mapping v2 records reconstructed with identical canonical mapping/projection digests; 27 native-only BHSA rows verified against immutable coverage evidence and never given a shared target; unit tests for drift and trust-boundary failures; one focused test command, no per-mapping release/version/workflow.
