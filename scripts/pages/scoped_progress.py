"""Read-only scoped census accounting; XML remains the mapping authority."""
from collections import defaultdict
import re

ONTOLOGIES = ("OLiA", "OntoLex-Lemon", "LRMoo", "CIDOC CRM", "CRMtex", "SKOS", "CRMinf", "Other")
POSITIVE = {"exact", "close", "broader", "narrower", "related"}
# Explicit namespace prefixes, not substring matching or dereferencing.
PREFIXES = {
    "OLiA": ("http://purl.org/olia/", "https://purl.org/olia/"),
    "OntoLex-Lemon": ("http://www.w3.org/ns/lemon/ontolex#", "https://www.w3.org/ns/lemon/ontolex#"),
    "LRMoo": ("http://iflastandards.info/ns/lrm/lrmoo/", "https://iflastandards.info/ns/lrm/lrmoo/"),
    "CIDOC CRM": ("http://www.cidoc-crm.org/cidoc-crm/", "https://www.cidoc-crm.org/cidoc-crm/"),
    "CRMtex": ("http://www.cidoc-crm.org/extensions/crmtex/", "https://www.cidoc-crm.org/extensions/crmtex/"),
    "SKOS": ("http://www.w3.org/2004/02/skos/core#", "https://www.w3.org/2004/02/skos/core#"),
    "CRMinf": ("http://www.cidoc-crm.org/extensions/crminf/", "https://www.cidoc-crm.org/extensions/crminf/"),
}


def ontology(iri):
    return next((name for name, prefixes in PREFIXES.items()
                 if any(iri.startswith(prefix) for prefix in prefixes)), "Other")


def compatible(inventory, source, version):
    if not inventory or inventory.get("schema_version") != 2 or not version:
        return False
    if inventory.get("catalog_version") != version:
        return False
    repo = source.split("@", 1)[0].split(":", 1)[0]
    if repo != inventory.get("repository"):
        return False
    pin = re.search(r"@([a-f0-9]{40})(?::|$)", source)
    return not pin or inventory.get("revision") == pin.group(1)


def observed_items(inventory):
    """Yield (kind, node, feature, value, from, to), frequency.

    Feature and node counts are observations of different types; never sum
    their frequencies into a token-coverage denominator.
    """
    for node, count in inventory["node_types"].items():
        yield ("node", node, None, None, None, None), count
    for feature, info in inventory["node_features"].items():
        for node, scope in info["scopes"].items():
            yield ("feature", node, feature, None, None, None), scope["count"]
            if scope.get("value_domain") == "complete_observed":
                for value, count in scope["values"].items():
                    yield ("value", node, feature, value, None, None), count
    for feature, info in inventory["edge_features"].items():
        for pair in info.get("pairs", ()):
            source, target = pair["from"], pair["to"]
            yield ("edge", None, feature, None, source, target), pair["count"]
            if pair.get("value_domain") == "complete_observed":
                for value, count in pair["values"].items():
                    yield ("edge_value", None, feature, value, source, target), count


def index_rows(rows, version):
    index = defaultdict(list)
    for row in rows:
        if row.kind != "entity" and row.corpus_version in (None, version):
            index[row.selector].append(row)
    return index


def matching(index, key):
    kind, node, feature, value, source, target = key
    if kind == "edge_value":
        return []  # Current XML has no individual valued-edge selector.
    if kind == "feature":
        # A feature-only declaration is a statement about the feature as a
        # whole; it can account for its observed scopes, not its values.
        return index.get(key, []) + index.get((kind, None, feature, None, None, None), [])
    if kind == "edge":
        # Explicit directions constrain coverage; omitted endpoints are generic.
        return [r for s in (source, None) for t in (target, None)
                for r in index.get((kind, None, feature, None, s, t), ())]
    return index.get(key, [])


def assessment(rows):
    if any(r.relation == "exact" for r in rows):
        return "exact"
    if any(r.relation in POSITIVE for r in rows):
        return "qualified"
    if rows:
        return "nonpositive"
    return "unreviewed"


def counts(items, index):
    result = dict(total=0, exact=0, qualified=0, nonpositive=0, unreviewed=0,
                  positive=0, reviewed=0, occurrences=0, positive_occurrences=0,
                  reviewed_occurrences=0)
    for key, frequency in items:
        status = assessment(matching(index, key))
        result["total"] += 1
        result[status] += 1
        result["occurrences"] += frequency
        if status != "unreviewed":
            result["reviewed"] += 1
            result["reviewed_occurrences"] += frequency
        if status in {"exact", "qualified"}:
            result["positive"] += 1
            result["positive_occurrences"] += frequency
    return result


KINDS = {"node": "node_types", "feature": "node_features", "value": "node_values",
         "edge": "edge_pairs", "edge_value": "edge_values"}


def scoped_progress(rows, inventory, source, version):
    if not compatible(inventory, source, version):
        return None
    index = index_rows(rows, version)
    items = list(observed_items(inventory))
    result = {label: counts([(key, freq) for key, freq in items if key[0] == kind], index)
              for kind, label in KINDS.items()}
    result.update(tf_version=inventory["tf_version"], catalog_version=version,
                  revision=inventory["revision"], tf_files_sha256=inventory["tf_files_sha256"])
    result["cross_version_edges"] = sorted(f for f, info in inventory["edge_features"].items()
                                           if info.get("scope_status") == "cross_version")
    result["overflow_domains"] = sorted([node, f] for f, info in inventory["node_features"].items()
                                         for node, s in info["scopes"].items()
                                         if s.get("value_domain") == "overflow")
    result["edge_overflow_domains"] = sorted([f, p["from"], p["to"]]
        for f, info in inventory["edge_features"].items() for p in info.get("pairs", ())
        if p.get("value_domain") == "overflow")
    outside, unmeasured, guarded = [], [], []
    for key, rs in index.items():
        kind, node, feature, value, _, _ = key
        scope = inventory["node_features"].get(feature, {}).get("scopes", {}).get(node)
        if kind == "value":
            if scope is None:
                outside.append([node, feature, value])
            elif scope.get("value_domain") != "complete_observed":
                unmeasured.append([node, feature, value])
            elif value not in scope["values"]:
                outside.append([node, feature, value])
        elif kind == "node" and feature:
            guarded.append(dict(node=node, feature=feature, status=assessment(rs),
                                observations=scope["count"] if scope else 0,
                                node_count=inventory["node_types"].get(node, 0)))
    result.update(outside_values=sorted(outside), unmeasured_values=sorted(unmeasured),
                  guarded_nodes=sorted(guarded, key=lambda x: (x["node"], x["feature"])))
    # Include every scoped categorical domain (even never mapped) and missing
    # native values so researchers can identify the next mapping batch.
    result["domains"] = []
    for feature, info in sorted(inventory["node_features"].items()):
        for node, scope in sorted(info["scopes"].items()):
            if scope.get("value_domain") != "complete_observed":
                continue
            domain = [(("value", node, feature, value, None, None), freq)
                      for value, freq in scope["values"].items()]
            result["domains"].append(dict(node=node, feature=feature,
                **counts(domain, index),
                unreviewed_values=sorted(key[3] for key, _ in domain if not matching(index, key))))
    result["unreviewed_items"] = [
        list(key) for key, _ in items if not matching(index, key)]
    return result


def rule_matches(rule, key):
    kind, node, feature, _, source, target = key
    return (kind == rule["kind"]
            and ("nodes" not in rule or node in rule["nodes"])
            and ("features" not in rule or feature in rule["features"])
            and ("from" not in rule or source in rule["from"])
            and ("to" not in rule or target in rule["to"]))


def eligible_progress(rows, inventory, policy, version):
    """Partial, researched applicability, never a complete ontology denominator.

    A target to one ontology cannot count as a disposition for another. Global
    native-only/unsupported and ambiguity are displayed separately, not silently
    credited as ontology-specific decisions.
    """
    index = index_rows(rows, version)
    items = list(observed_items(inventory))
    result = {}
    for model, rules in policy.items():
        if model not in ONTOLOGIES[:-1]:
            raise ValueError(f"Unknown applicability ontology: {model}")
        chosen = set()
        unmatched = []
        for rule in rules:
            matched = {key for key, _ in items if rule_matches(rule, key)}
            if not matched:
                unmatched.append(rule)
            chosen.update(matched)
        stat = dict(eligible=len(chosen), exact=0, qualified=0, global_nonpositive=0,
                    ambiguous=0, other_target=0, unreviewed=0, unmatched_rules=unmatched)
        for key in chosen:
            rs = matching(index, key)
            own = [r for r in rs if r.relation in POSITIVE and ontology(r.target) == model]
            if own:
                status = assessment(own)
            elif any(r.relation in POSITIVE for r in rs):
                status = "other_target"
            elif any(r.relation == "ambiguous" for r in rs):
                status = "ambiguous"
            elif rs:
                status = "global_nonpositive"
            else:
                status = "unreviewed"
            stat[status] += 1
        stat["positive"] = stat["exact"] + stat["qualified"]
        result[model] = stat
    return result
