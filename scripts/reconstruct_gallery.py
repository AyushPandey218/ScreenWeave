import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('backend').resolve()))
from reconstruct import reconstruct,export
for name in ('rounded','pricing','product','dashboard','profile','banner'):
    folder=Path('frontend/public/examples');layout=reconstruct((folder/(name+'.png')).read_bytes());(folder/(name+'.json')).write_text(json.dumps(layout),encoding='utf-8');html,css=export(layout);Path('reports/gallery',name+'-draft.html').write_text(html.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>'),encoding='utf-8');print(name,len(layout['elements']),flush=True)
