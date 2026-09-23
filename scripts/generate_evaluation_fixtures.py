"""Generate redistributable synthetic fixtures. No external photographs or datasets."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.typography import FONT_FAMILIES
OUT=ROOT/'tests/fixtures/evaluation'
OUT.mkdir(parents=True,exist_ok=True)
def font(family,size):
    return ImageFont.truetype(str(next(p for p in FONT_FAMILIES[family][0] if p.exists())),size)
for name in ('login','rounded-controls'):
    Image.open(ROOT/f'tests/fixtures/{name}.png').save(OUT/f'{name}.png')
rng=np.random.default_rng(218)
for name in ('image-cards','image-banner'):
    im=Image.new('RGB',(840,360),'#141918');d=ImageDraw.Draw(im)
    for x in (20,440):
        texture=Image.fromarray(rng.integers(0,256,(220,380,3),dtype=np.uint8)).filter(ImageFilter.GaussianBlur(.6))
        im.paste(texture,(x,20));d.text((x,260),'Explore the collection',font=font('sans-serif',22),fill='white')
        if name=='image-banner':
            d.rounded_rectangle((x+20,95,x+330,145),radius=8,fill='#ffffff');d.text((x+30,103),'A new perspective',font=font('sans-serif',24),fill='#172e30')
    im.save(OUT/f'{name}.png')
for family,name in [('serif','serif-panel'),('monospace','monospace-panel')]:
    im=Image.new('RGB',(800,420),'#eef2ed');d=ImageDraw.Draw(im)
    d.rounded_rectangle((40,35,760,385),radius=20,fill='white',outline='#aab8ad',width=2)
    d.text((75,75),'Build something useful',font=font(family,34),fill='#172e30')
    d.text((75,150),'Ideas become editable interfaces.',font=font(family,23),fill='#344d43')
    d.text((75,205),'Review. Refine. Export.',font=font(family,23),fill='#344d43')
    d.rounded_rectangle((75,285,340,340),radius=18,fill='#245b46')
    d.text((110,297),'Start building',font=font(family,24),fill='white')
    im.save(OUT/f'{name}.png')
print(f'Generated 6 synthetic cases in {OUT}')
