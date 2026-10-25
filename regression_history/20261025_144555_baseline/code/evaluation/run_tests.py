import json
import time
import unittest
from pathlib import Path

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    suite=unittest.defaultTestLoader.discover(str(root/'code/evaluation'),pattern='test_*.py')
    started=time.perf_counter();result=unittest.TextTestRunner(verbosity=2).run(suite)
    record={'tests_run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors),'failures':len(result.failures),'errors':len(result.errors),'seconds':round(time.perf_counter()-started,4)}
    target=root/'evaluation_artifacts/tests.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(record,indent=2),encoding='utf8')
    if not result.wasSuccessful():raise SystemExit(1)
