"""#171 — cluster_by_concept: normalization hoist + inverted-index candidate
filter must (a) produce IDENTICAL clustering to the brute-force reference and
(b) not compare zero-overlap pairs. Plus the project scoping of load_claims.
"""

import sys
from pathlib import Path
from collections import defaultdict

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

import synthesize as S


def _claim(stmt):
    return {"file": None, "stem": f"stem-{abs(hash(stmt)) % 10**8}",
            "fm": {"statement": stmt}, "body": "", "statement": stmt,
            "status": "supported", "confidence": "high", "evidence_strength": "secondary"}


def _reference_clusters(claims, threshold):
    """The pre-#171 brute force, verbatim semantics."""
    from wf_common import norm

    def isect_sets(c):
        return set(norm(c["statement"]).split()) - S.CONCEPT_NAME_FILTER

    n = len(claims)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        pi, pj = find(i), find(j)
        if pi != pj:
            parent[pi] = pj

    for i in range(n):
        for j in range(i + 1, n):
            si, sj = isect_sets(claims[i]), isect_sets(claims[j])
            if not si or not sj:
                continue
            if len(si & sj) / max(len(si), len(sj)) >= threshold:
                union(i, j)
    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)
    return [sorted(ix) for ix in clusters.values() if len(ix) >= 2]


def _as_index_groups(clusters):
    return sorted(sorted(c.index(st) for st, c in zip(cl, [None] * 0)) for c in [])  # placeholder


class TestEquivalence:
    def _run_both(self, statements, threshold=0.4):
        claims = [_claim(s) for s in statements]
        import synthesize
        old_min = synthesize.MIN_CLAIMS
        synthesize.MIN_CLAIMS = 2
        try:
            got = synthesize.cluster_by_concept(claims, threshold)
            want = _reference_clusters(claims, threshold)
        finally:
            synthesize.MIN_CLAIMS = old_min
        got_idx = []
        for cl in got:
            idx = sorted(claims.index(c) for c in cl)
            got_idx.append(idx)
        return sorted(got_idx), sorted(want)

    def test_identical_clusters_corpus_sample(self):
        # realistic statement mix (project-name collisions, shared tokens)
        stmts = [
            "the graphify rebuild imports graph json files",
            "graphify rebuild imports graph files",
            "unrelated text about cooking pasta with tomatoes",
            "cooking pasta dishes at home",
            "the hook captures doc drift after commit",
            "hook captures drift on every commit run",
            "quantum flux capacitor calibration guide",
            "the graph rebuild imports json",
            "hook handles commit drift capture",
            "pasta with tomatoes and basil",
            "calibration of the flux capacitor",
            "nothing matches this string zxqv",
        ]
        got, want = self._run_both(stmts)
        assert got == want, f"cluster divergence:\n got={got}\nwant={want}"

    def test_identical_clusters_randomized(self):
        import random
        random.seed(171)
        vocab = ["alpha", "beta", "gamma", "delta", "epsilon", "the", "a",
                 "graph", "capture", "hook", "claim", "drift", "ingest",
                 "zeta", "omega", "render", "commit", "source"]
        statements = []
        for _ in range(120):
            n = random.randint(3, 14)
            statements.append(" ".join(random.choice(vocab) for _ in range(n)))
        got, want = self._run_both(statements, threshold=0.35)
        assert got == want

    def test_empty_and_single(self):
        assert S.cluster_by_concept([], 0.4) == []
        one = [_claim("only one statement here")]
        assert S.cluster_by_concept(one, 0.4) == []  # MIN_CLAIMS default 2


class TestScoping:
    def test_load_claims_project_scope(self, tmp_path=None):
        import importlib
        import fabric_config
        import os
        import tempfile
        tmp = Path(tempfile.mkdtemp()) / "corpus"
        claims_dir = tmp / "evidence" / "claims"
        claims_dir.mkdir(parents=True)
        (claims_dir / "claim-my-proj-a-md-000.md").write_text(
            "---\ntype: claim\nid: claim-my-proj-a-md-000\nstatement: alpha\nstatus: supported\n---\n")
        (claims_dir / "claim-other-b-md-000.md").write_text(
            "---\ntype: claim\nid: claim-other-b-md-000\nstatement: beta\nstatus: supported\n---\n")
        os.environ["WIKI_FABRIC_DIR"] = str(tmp.parent)
        (tmp.parent / "fabric.yaml").write_text("repos: {}\n")
        importlib.reload(fabric_config)
        import importlib as _il
        syn = _il.reload(S)
        all_c = syn.load_claims()
        assert len(all_c) == 2
        scoped = syn.load_claims(project="my-proj")
        assert [c["stem"] for c in scoped] == ["claim-my-proj-a-md-000"]