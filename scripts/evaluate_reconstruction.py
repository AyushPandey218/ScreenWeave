"""Run one implementation in an isolated process; reconstruction time excludes exports."""
import argparse,json,sys,time,platform,hashlib
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--backend',required=True);parser.add_argument('--output',required=True);parser.add_argument('--label',required=True);parser.add_argument('--runs',type=int,default=3);args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(args.backend).resolve()))
from reconstruct import reconstruct,export
from PIL import Image
out=Path(args.output);out.mkdir(parents=True,exist_ok=True);rows=[]
for source in sorted((ROOT/'tests/fixtures/evaluation').glob('*.png')):
    payload=source.read_bytes();times=[]
    for _ in range(args.runs):
        start=time.perf_counter();layout=reconstruct(payload);times.append(time.perf_counter()-start)
    html,css=export(layout)
    (out/(source.stem+'.html')).write_text(html.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>'),encoding='utf-8')
    (out/(source.stem+'.json')).write_text(json.dumps(layout,indent=2),encoding='utf-8')
    rows.append({'case':source.stem,'width':layout['viewport']['width'],'height':layout['viewport']['height'],'seconds':times,'elements':len(layout['elements']),'sha256':hashlib.sha256(payload).hexdigest()})
    print(args.label,source.stem,round(sum(times)/len(times),3),flush=True)
(out/'timings.json').write_text(json.dumps({'label':args.label,'python':sys.version,'platform':platform.platform(),'runs':args.runs,'cases':rows},indent=2),encoding='utf-8')
