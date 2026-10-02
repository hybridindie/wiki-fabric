import os, subprocess, sys
from pathlib import Path

fabric = Path(os.environ['WF_FABRIC'])
sys.path.insert(0, str(fabric / 'scripts' / 'lib'))  # shared helpers (wf_common)
from wf_common import project_slug as _psl  # canonical fold (#158 S3)
slug = _psl(os.environ['WF_SLUG'])  # underscore repo dirs fold; capture/ingest resolve canonically
py = sys.executable

# 1. Capture (sha256 drift vs recorded sources; exit 2 == drift)
r = subprocess.run([py, str(fabric / 'scripts/cmd/capture.py'), slug,
                    '--project-root', os.getcwd(), '--quiet'],
                   capture_output=True).returncode
if r not in (0, 2):
    print(f'[wf hook] capture failed (exit {r}) — run: wf capture {slug}', flush=True)
    sys.exit(1)
if r == 0:
    print('[wf hook] no doc drift — capture skipped', flush=True)
    # doc capture skipped, but CODE changes still drive the graphify cycle
    # (fall through to steps 3-4 rather than exiting)

if r == 2:
    # 2. Ingest drift. LLM only when --extract-claims was enabled at install
    #    time (WIKI_HOOK_EXTRACT=1); otherwise sources are recorded without
    #    claims and the agent ingests interactively on next session.
    ingest_args = [py, str(fabric / 'scripts/cmd/ingest.py'), '--changed', slug]
    if os.environ.get('WIKI_HOOK_EXTRACT', '').lower() in ('1', 'true', 'yes'):
        ingest_args.append('--extract-claims')
    print('[wf hook] captured drift — ingesting...', flush=True)
    subprocess.run(ingest_args)

# 3. After intake, persist the pending-HITL manifest (promotion dossiers,
#    domain proposals, stale claims) so ANY AI harness can surface pending
#    decisions at session start by reading registry/pending-gate.md.
subprocess.run([py, str(fabric / 'scripts/cmd/gate.py'), '--quiet', '--write-manifest'])

# 4. Graphify BRIDGE steps — the graph rebuild itself belongs to graphify's
#    own hook (`graphify hook install` appends a post-commit block that runs
#    its incremental watcher with timeout/resource guards; do not duplicate
#    it here). This step consumes that output: import the fresh graph into
#    the corpus, enrich claims with graph_edges, run the staleness diff.
#    Gated on: bridge present, integration enabled (bridge refuses loudly
#    to the log otherwise). Note ordering: graphify's rebuild runs detached
#    too, so a tiny sleep-free retry on import covers the rebuild finishing.
bridge = fabric / 'scripts/harness/graphify-bridge.py'
if not bridge.exists():
    sys.exit(0)
r = subprocess.run([py, str(bridge), '--status', '--repo', slug],
                   capture_output=True, text=True, timeout=60)
if 'not enabled' in r.stdout:
    sys.exit(0)  # graphify off — quiet, by design
import time as _time
for attempt in range(6):
    r = subprocess.run([py, str(bridge), '--import', '--repo', slug],
                       capture_output=True, text=True, timeout=300)
    if 'no graph' not in r.stdout or attempt == 2:
        break
    _time.sleep(2)  # graphify's detached rebuild may still be writing
if 'no graph' in r.stdout:
    print('[wf hook] graphify graph not ready — bridge steps skipped', flush=True)
    sys.exit(0)
print('[wf hook] ' + r.stdout.strip().splitlines()[-1][:120], flush=True)
for step in ('--enrich', '--diff'):
    r = subprocess.run([py, str(bridge), step, '--repo', slug],
                       capture_output=True, text=True, timeout=300)
    if r.stdout.strip():
        print('[wf hook] ' + r.stdout.strip().splitlines()[-1][:120], flush=True)
