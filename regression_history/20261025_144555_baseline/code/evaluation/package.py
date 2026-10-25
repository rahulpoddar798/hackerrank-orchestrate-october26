"""Create an allowlisted, reproducible submission archive; no dataset or cache."""
from pathlib import Path
import zipfile

def package(root):
    included=[root/'README.md']+[p for p in (root/'code').rglob('*') if p.is_file() and p.suffix in {'.py','.ps1','.md','.txt'} and '__pycache__' not in p.parts]
    target=root/'code.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(included):
            info=zipfile.ZipInfo(p.relative_to(root).as_posix(),date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
        # Both documented report layouts are included for evaluator compatibility.
        for name in ['evaluation_report.md','usage_report.md']:
            info=zipfile.ZipInfo('evaluation/'+name,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(root/'code/evaluation'/name).read_bytes())
    print(f'Created {target.name}: {len(included)+2} entries, {target.stat().st_size} bytes')

if __name__=='__main__':package(Path(__file__).resolve().parents[2])
