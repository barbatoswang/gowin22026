from pathlib import Path
import urllib.request,json,hashlib
root=Path(__file__).resolve().parent
for item in json.loads((root/'sources.json').read_text(encoding='utf8'))['files']:
    p=root/item['file']
    if p.exists():
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];continue
    data=urllib.request.urlopen(item['url']).read()
    assert hashlib.sha256(data).hexdigest()==item['sha256']
    p.write_bytes(data)
print('PASS source download hashes')
