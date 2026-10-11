# I-028C — pin the original OntoLex Core RDF/XML, not a guessed ontology term list

**Issue:** #350, under #265 / P-004 #202. **Research gate:** examined actual original upstream OWL bytes, alongside the final [W3C Community Group Report (10 May 2016)](https://www.w3.org/2016/05/ontolex/), and ontoTF's installed OLiA source/lock and `ontology-lock.schema.json`.

## Source identity, integrity and redistributability

- Canonical source repository: `ontolex/ontolex`, exact commit `d6f840f40a05b76cbd8c10b9472ddd097371d610`, file `Ontologies/ontolex.owl`.
- Original Git blob SHA-1: `10783b4c747bbc5f08fbae8f4169d6e02fc22565` (over the **54,553 UTF-8 bytes**).
- Original file SHA-256: `76e4c74fae4013944f60701df83828836c22a7f19c8cc8f72f994e321d12efd9`; reproducibly verify both hashes from installed raw OWL and detect unreviewed byte changes.
- The RDF/XML ontology header explicitly carries `<dc:rights>CC-Zero</dc:rights>` and `cc:license rdf:resource="https://creativecommons.org/publicdomain/zero/1.0/"`. This evidence supports distribution of the ontology file as CC0. It does **not** grant rights to independently licensed corpus data.
- The OWL is a **source XML document with a DTD-internal entity declaration**; Python stdlib ElementTree can parse its internal `&ontolex;` etc. without network resolution. Avoid external fetching/parsing at runtime.
- Ontology versionInfo reads `1.1` and `dc:modified` reads `2016-01-10` in the pinned XML. The source commit controls the snapshot identity; a mutable `master` pointer never does.

## Verified original model declarations

- `ontolex:LexicalEntry` and `ontolex:Form` are separately declared `owl:Class`, along with `LexicalSense` and `LexicalConcept`.
- `ontolex:lexicalForm` is an `owl:ObjectProperty`, domain `LexicalEntry`, range `Form`. `canonicalForm` is its subproperty.
- `ontolex:writtenRep` is an `owl:DatatypeProperty`, domain `Form`, range `rdf:langString`.
- The `LexicalEntry` subclass restriction has `owl:onProperty lexicalForm`, `owl:onClass Form` and `owl:minQualifiedCardinality 1`. The `Form` subclass restriction requires at least one `writtenRep` langString.
- Thus **none of the BHSA/Syriac gloss and lemma strings by themselves is an instance of `Form` or `LexicalSense`**. The OntoLex class identity is necessary but insufficient for a reviewed BHSA lexical-entry publication.

## Decision and alternatives

Vendor exactly the original OWL snapshot and its source-bound ontology lock. Mark this as an **evidence-only ontology reference**, not a released BHSA mapping or installed shared pivot capability. Keep immutable historical OLiA files untouched. Testing must parse real RDF/XML terms and restrictions and independently verify SHA-256/Git blob SHA-1; string substring checks and developer-authored assertions alone are insufficient.

**Rejected:** a hand-authored `owl:Class` stub pretending to be upstream; a mutable download URL without commit pin; a reused OLiA lock ID; a project-generated OWL with inferred BHSA word→Form relations; treating OWL license metadata as permission to redistribute any TF corpus.
