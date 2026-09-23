"""Optional narrow-screen stacking of inferred groups; not responsive intent recovery."""

def groups(layout):
    elements=layout['elements']; by_id={e['id']:e for e in elements}
    assigned={}
    area=layout['viewport']['width']*layout['viewport']['height']
    for e in elements:
        root=e; seen={e['id']}
        while root.get('parent_id') in by_id:
            parent=by_id[root['parent_id']]
            if parent['id'] in seen or (parent['type']=='container' and parent['width']*parent['height']>area*.8):
                break
            seen.add(parent['id']);root=parent
        assigned.setdefault(root['id'],[]).append(e)
    result=[]
    for items in assigned.values():
        x=min(e['x'] for e in items);y=min(e['y'] for e in items)
        w=max(e['x']+e['width'] for e in items)-x;h=max(e['y']+e['height'] for e in items)-y
        result.append({'x':x,'y':y,'width':w,'height':h,'ids':[e['id'] for e in items]})
    return sorted(result,key=lambda g:(round(g['y']/24),g['x']))


def responsive_css(layout):
    if not layout.get('responsive'):
        return ''
    by_id={e['id']:e for e in layout['elements']}
    rules=['.responsive-group{display:contents}','@media(max-width:640px){','.page{display:flex;flex-direction:column;gap:16px;width:100%;height:auto;min-height:100vh;padding:16px;overflow:hidden}', '.responsive-group{display:block;position:relative;width:100%;container-type:inline-size;flex:none;align-self:center}']
    for i,g in enumerate(groups(layout)):
        w,h=g['width'],g['height']
        if len(g['ids'])==1 and by_id[g['ids'][0]]['type']=='container' and w*h>layout['viewport']['width']*layout['viewport']['height']*.8:
            rules.append(f'.responsive-group[data-group="{i}"]{{display:none}}')
            continue
        rules.append(f'.responsive-group[data-group="{i}"]{{max-width:{w}px;aspect-ratio:{w}/{h}}}')
        for identity in g['ids']:
            e=by_id[identity]
            rules.append(f"#{identity}{{left:{(e['x']-g['x'])/w*100:.5f}%;top:{(e['y']-g['y'])/h*100:.5f}%;width:{e['width']/w*100:.5f}%;height:{e['height']/h*100:.5f}%;}}")
            if e['type'] in ('text','button'):
                size=e.get('font_size',16)
                rules.append(f'#{identity}{{font-size:{size/w*100:.5f}cqw;}}')
    return '\n'.join(rules+['}'])


def wrap_markup(layout,markup):
    if not layout.get('responsive'):
        return markup
    by_id=dict(zip((e['id'] for e in layout['elements']),markup))
    return ['<section class="responsive-group" data-group="'+str(i)+'">'+''.join(by_id[k] for k in g['ids'])+'</section>' for i,g in enumerate(groups(layout))]
