# Fixture B — threading test log (excerpt)

Engine v4.7.2.stable

  PASS: threaded mode is on by default
  PASS: chunks streamed with threads on (25)
  PASS: threaded-generated blocks match sync baseline (1075 checked, 0 mismatch)
  PASS: no stale chunks after teleport (0 strays)
  ... (12 more PASS lines, all happy-path parity checks) ...
  FAIL: baseline thread stress: 800 concurrent calls match baseline (244 mismatch)
threading test: 17 passed, 1 failed
libc++abi: terminating due to uncaught exception of type std::__1::system_error: recursive_mutex lock failed: Invalid argument