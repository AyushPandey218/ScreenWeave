"""Compute full-frame visual error and plot measured comparisons; never fabricate accuracy."""
import csv,json,statistics
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'docs/evaluation';out.mkdir(exist_ok=True,parents=True)
rows=[];metadata={}
for variant in ('baseline','current'):
    folder=ROOT/'reports/evaluation'/variant
    data=json.loads((folder/'timings.json').read_text(encoding='utf-8-sig'));metadata[variant]={k:v for k,v in data.items() if k!='cases'}
    for case in data['cases']:
        source=np.asarray(Image.open(ROOT/'tests/fixtures/evaluation'/f"{case['case']}.png").convert('RGB')).astype(float)
        actual=np.asarray(Image.open(folder/f"{case['case']}.png").convert('RGB')).astype(float)
        error=np.abs(source-actual)
        rows.append({**case,'variant':variant,'mae_rgb_255':round(float(error.mean()),4),'pixels_over_25_pct':round(float((error.mean(axis=2)>25).mean()*100),4),'median_seconds':round(statistics.median(case['seconds']),4)})
(out/'results.json').write_text(json.dumps({'metadata':metadata,'cases':rows},indent=2),encoding='utf-8')
with (out/'results.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['case','variant','mae_rgb_255','pixels_over_25_pct','median_seconds','elements'];writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f7faf5','axes.facecolor':'#f7faf5'})
cases=[r['case'] for r in rows if r['variant']=='baseline'];x=np.arange(len(cases));fig,axes=plt.subplots(2,1,figsize=(11,8),layout='constrained')
for variant,color,offset in [('baseline','#8c989d',-.19),('current','#447758',.19)]:
    items=[r for r in rows if r['variant']==variant]
    axes[0].bar(x+offset,[r['mae_rgb_255'] for r in items],.36,label=variant.title(),color=color)
    med=np.array([r['median_seconds'] for r in items]);low=np.array([min(r['seconds']) for r in items]);high=np.array([max(r['seconds']) for r in items])
    axes[1].bar(x+offset,med,.36,color=color,yerr=[np.maximum(0,med-low),np.maximum(0,high-med)],capsize=3)
axes[0].set_title('Visual reconstruction error · lower is better',loc='left',fontweight='bold');axes[0].set_ylabel('Mean absolute RGB error (0–255)');axes[0].legend(frameon=False)
axes[1].set_title('Local reconstruction time · median of 3 runs',loc='left',fontweight='bold');axes[1].set_ylabel('Seconds (range shown)')
for ax in axes:ax.set_xticks(x,cases,rotation=15,ha='right');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.suptitle('ScreenWeave | Measured baseline comparison',fontsize=18,fontweight='bold',x=.05,ha='left')
fig.supxlabel('6 synthetic fixtures · baseline 23c5ebd · same machine and OCR runtime · no hosted/network time',fontsize=9)
fig.savefig(out/'comparison.png',dpi=180);fig.savefig(out/'comparison.svg');plt.close(fig)
fig,axes=plt.subplots(2,3,figsize=(12,5),layout='constrained')
for i,name in enumerate(('image-cards','serif-panel')):
    for j,(label,folder) in enumerate([('Source',ROOT/'tests/fixtures/evaluation'),('Baseline',ROOT/'reports/evaluation/baseline'),('Current',ROOT/'reports/evaluation/current')]):
        axes[i,j].imshow(Image.open(folder/f'{name}.png'));axes[i,j].set_title(label+' · '+name,fontsize=10);axes[i,j].axis('off')
fig.savefig(out/'visual-comparison.png',dpi=160);plt.close(fig)
print(json.dumps({v:{'mean_mae':round(statistics.mean(r['mae_rgb_255'] for r in rows if r['variant']==v),3),'mean_case_median_seconds':round(statistics.mean(r['median_seconds'] for r in rows if r['variant']==v),3)} for v in ('baseline','current')},indent=2))
