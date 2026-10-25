"""Local document extraction. Cache keys depend on bytes and extractor version."""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import csv
import io
from collections import defaultdict
from pathlib import Path

VERSION = "document-v1"
STATS={'ocr_calls':0,'ocr_cache_hits':0,'pdf_documents':0}

def ocr(path: Path, cache: Path) -> dict:
    key = hashlib.sha256(path.read_bytes() + VERSION.encode()).hexdigest()
    target = cache / (key + ".json")
    cache.mkdir(parents=True, exist_ok=True)
    if target.exists():
        STATS['ocr_cache_hits']+=1
        return json.loads(target.read_text(encoding="utf8"))
    STATS['ocr_calls']+=1
    if os.name == "nt":
        result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(Path(__file__).with_name("windows_ocr.ps1")), "-ImagePath", str(path.resolve())], capture_output=True, timeout=90)
        if result.returncode:
            raise RuntimeError("Windows OCR failed: " + result.stderr.decode("utf8", errors="replace")[-1200:])
        data = json.loads(result.stdout.decode("utf-8-sig"))
    elif shutil.which("tesseract"):
        result = subprocess.run(["tesseract", str(path), "stdout", "--psm", "11", "tsv"], capture_output=True, text=True, check=True, timeout=90)
        groups=defaultdict(list)
        for row in csv.DictReader(io.StringIO(result.stdout),delimiter='\t'):
            if row.get('text','').strip() and int(row['level'])==5:
                groups[(row['block_num'],row['par_num'],row['line_num'])].append({'text':row['text'],'x':int(row['left']),'y':int(row['top']),'width':int(row['width']),'height':int(row['height'])})
        lines=[{'text':' '.join(w['text'] for w in ww),'words':ww} for ww in groups.values()]
        data = {"text": '\n'.join(line['text'] for line in lines), "engine": "tesseract", "lines": lines}
    else:
        raise RuntimeError("Image evidence requires Windows OCR or the tesseract executable.")
    target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    return data

def pdf_pages(path: Path) -> list[str]:
    STATS['pdf_documents']+=1
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError("Install dependencies: python -m pip install -r code/requirements.txt") from exc
    with pdfium.PdfDocument(str(path)) as document:
        return [page.get_textpage().get_text_range().replace("\r\r\n", "\n").replace("\r\n", "\n") for page in document]

def render_pdf(path: Path, output: Path) -> list[Path]:
    """Write PNGs without Pillow; PDFium supplies pixels, stdlib encodes PNG."""
    import pypdfium2 as pdfium
    import ctypes, struct, zlib
    output.mkdir(parents=True, exist_ok=True)
    results = []
    def chunk(kind, content):
        return struct.pack(">I",len(content)) + kind + content + struct.pack(">I",zlib.crc32(kind+content))
    with pdfium.PdfDocument(str(path)) as document:
        for i, page in enumerate(document):
            bitmap = page.render(scale=1.6, rev_byteorder=True)
            bpp = bitmap.stride // bitmap.width
            raw = bytes(bitmap.buffer)
            scan = b"".join(b"\0" + raw[y*bitmap.stride:y*bitmap.stride+bitmap.width*bpp] for y in range(bitmap.height))
            color = 6 if bpp == 4 else 2
            png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB",bitmap.width,bitmap.height,8,color,0,0,0)) + chunk(b"IDAT",zlib.compress(scan)) + chunk(b"IEND",b"")
            target = output / f"{path.stem}-{i+1}.png"
            target.write_bytes(png)
            results.append(target)
    return results
