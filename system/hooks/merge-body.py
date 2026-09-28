import os, subprocess, sys
from pathlib import Path

fabric = Path(os.environ['WF_FABRIC'])
slug = os.environ['WF_SLUG']
py = sys.executable

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
    ingest_args = [py, str(fabric / 'scripts/cmd/ingest.py'), '--changed', slug]
    if os.environ.get('WIKI_HOOK_EXTRACT', '').lower() in ('1', 'true', 'yes'):
        ingest_args.append('--extract-claims')
    print('[wf hook] captured drift — ingesting...', flush=True)
    subprocess.run(ingest_args)

# Surface pending HITL decisions (promotion/domain proposals, stale claims)
# after a merge too — merge is a common moment for new upstream evidence.
subprocess.run([py, str(fabric / 'scripts/cmd/gate.py'), '--quiet', '--write-manifest'])

# 5. Merge-time capture-git (#85): the PR narrative (description, review
#    discussion) is the *why* behind the diff the merge carries. Gated on a
#    GitHub remote; fire-and-forget — never blocks, failures just log.
try:
    from fabric_config import get_config, get_all_repo_names, resolve_repo_path
    cfg = get_config()
except Exception as _e:
    print(f'[wf hook] capture-git skipped (config unreadable: {_e})', flush=True)
    cfg = None
if cfg is not None:
    for repo_name in get_all_repo_names(cfg):
        if repo_name != slug:
            continue  # this hook fires in the merged repo only
        repo_path = resolve_repo_path(cfg, repo_name)
        if repo_path is None or not (repo_path / '.git').exists():
            continue
        sys.path.insert(0, str(fabric / 'scripts' / 'cmd'))
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location('capture_git', fabric / 'scripts/cmd/capture-git.py')
            _cg = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_cg)
            owner_repo = _cg.github_repo_from_remote(repo_path)
            if not owner_repo:
                break  # local-only repo — no gh capture, keep working
            r = subprocess.run(
                [py, str(fabric / 'scripts/cmd/capture-git.py'), slug,
                 '--repo', owner_repo, '--since-state', '--limit', '10'],
                capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                print(f'[wf hook] capture-git failed (exit {r.returncode})', flush=True)
            else:
                tail = [l for l in r.stdout.strip().splitlines() if l.strip()]
                print('[wf hook] capture-git: ' + (tail[-1] if tail else 'ok'), flush=True)
        except Exception as _e:
            print(f'[wf hook] capture-git error: {_e}', flush=True)
        break
