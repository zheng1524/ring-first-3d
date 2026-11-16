from _bootstrap import ROOT, args, emit
import io
import time
import unittest


def run():
    t = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_harness_contracts.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    return dict(status="PASS" if result.wasSuccessful() else "FAIL", tests=result.testsRun,
                failures=len(result.failures), errors=len(result.errors), seconds=time.monotonic()-t,
                log=stream.getvalue(), GT_read=False)


if __name__ == "__main__":
    a = args("Independent mathematical and boundary contract tests")
    result = run();emit(result, a.output)
    raise SystemExit(0 if result["status"] == "PASS" else 1)
