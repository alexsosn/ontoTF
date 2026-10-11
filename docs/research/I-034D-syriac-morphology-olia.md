# I-034D — 22 genuine Syriac morphology dispositions against OLiA

**Real semantics, not review architecture.** Issue #264 / #202, base `90d22551aba675a65f55bb700bede913bd2397bd`.

## Primary-source audit

Pinned ETCBC linksyr grammar `3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6/data/lib/syriac/word_grammar`:
- `ps` function is explicitly first/second/third (line **61**). TF denominator additionally observes `unknown`, *not* explicitly defined in the source.
- `st` has `cst=construct`, `abs=absolute`, `emph=emphatic` (line **95**). Denominator also contains `c`, `unknown`; those are not defined by that grammar table and must not be invented as synonyms.
- `vo` has `act=active`, `pas=passive` (**97**).
- `vs` stem is `pe=peal`, `pa=pael`, `af=afel` (**99**).
- `vt` verbal tense/form has `pf=perfect`, `ipf=imperfect`, `imp=imperative` (**101**), `inf=infinitive`, `ptc=participle` (**102**).
- `vpm` is a source vowel-pattern morpheme (**29**, **50**); its `p` symbol is shown on line 50, whereas `d`/`dp` in the TF inventory have no definition in the pinned grammar.

Original target corpus is independently pinned `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`, not the grammar source SHA. The frozen 74-item `p004-i027c2-syriac-adj-adv-v1` production denominator contains **22 observed values** over ps/st/vo/vpm/vs/vt, and none is already production accounted as a shared class. Existing reviewed gn/nu/sp categories are excluded rather than duplicated.

The actual *same-pinned* OLiA OWL snapshot `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/owl/core/olia.owl`, SHA-256 `5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd`, explicitly declares:
- PersonFeature classes `First` (4986), `Second` (4976), `Third` (4963), **not** corresponding PersonPronoun classes;
- Semitic construct state class `StatusConstructus` (6712, `rdf:ID`);
- grammatical `ActiveVoice` (9254), `PassiveVoice` (9272);
- `ImperativeVerb` (1373), `Infinitive` (1013), `Participle` (1072).

## 22 semantic dispositions

**Nine** source- and ontology-compatible exact category proposals: 3 person, 1 construct state (`st=cst`), 2 grammatical voice, 3 verb forms (`vt=imp/inf/ptc`). **Thirteen** values native-only pending evidence: `ps=unknown`; `st=abs/emph/c/unknown`; `vpm=p/d/dp`; `vs=pe/pa/af`; `vt=pf/ipf`. The lexical morphology behind Semitic `pf`/`ipf` is not synonymous with OLiA Perfect/Imperfect, whose original XML definitions are past-specific. OLiA Emphatic denotes emphasis, not the Semitic emphatic state. `vs` verbal stems have no verified matching exact OLiA classes; a shared string is not proof of semantics.

**Scope:** feature/value annotations on Syriac word nodes; no ontology equivalence of tokens, no invented lexeme/inflection entity identity, no source gloss invented for R-005-only codes. Output is an unreviewed research ledger and tests; not a runtime compiled mapping or an installed release. No new infrastructure ticket per class.

**Challenge:** verify R-005 observed values, original grammar line, OLiA XML actual class declarations, no artificial `c=construct` alias, no unsupported `vpm` mapping, and true absence of prior production review.
