"""Run the packaged source against all requests with a fresh extraction cache."""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2];(root/'tmp').mkdir(exist_ok=True)
    target=Path(tempfile.mkdtemp(prefix='package-smoke-',dir=root/'tmp'))
    with zipfile.ZipFile(root/'code.zip') as z:z.extractall(target)
    command=[sys.executable,str(target/'code/main.py'),'--dataset',str(root/'dataset'),'--output',str(target/'output.csv'),'--artifacts',str(target/'artifacts'),'--cache',str(target/'cache')]
    result=subprocess.run(command,cwd=target,capture_output=True,text=True,timeout=300)
    if result.returncode:raise RuntimeError(result.stderr[-2500:])
    actual=hashlib.sha256((target/'output.csv').read_bytes()).hexdigest();expected=hashlib.sha256((root/'output.csv').read_bytes()).hexdigest()
    run=json.loads((target/'artifacts/run.json').read_text())
    record={'passed':actual==expected,'same_output_sha256':actual==expected,'output_sha256':actual,'requests':run['requests'],'fresh_ocr_calls':run['local_extraction']['ocr_calls'],'ocr_cache_hits':run['local_extraction']['ocr_cache_hits'],'elapsed_seconds':run['elapsed_seconds'],'environment':'fresh source extraction and empty cache; isolated installed Python dependencies reused'}
    (root/'evaluation_artifacts/package_smoke.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record))
    if not record['passed']:raise SystemExit(1)
