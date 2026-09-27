"""sync_lib — sync.py's internals split by responsibility (#124.5b).

modules:
  policy — sync mode/evidence-PR policy + change-plane classification
           (pure logic; the most-tested surface)
  pr     — GitHub PR machinery (gh interaction, branch/PR creation,
           auto-merge policy)

sync.py remains the verb entry (cmd_init/setup/status/push/pull/resolve).
"""
