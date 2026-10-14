"""Per author type evidence for the Fly Cell Atlas mapping (both FCA projects).

For each distinct author type (10x Stringent + Smart-seq2 label transfer): the
authors' ontology ids with their current FBbt name / definition / obsolete status and
whether each is a cell type (is_a descendant of FBbt:00007002 'cell'); the authors'
broad class; cells per analysis; and scripted FBbt candidates (an 'adult X' variant
of the author term, replaced_by, exact label / exact-synonym matches of the type
name). Feeds the reports, the mapping agents and the scripted confirmations.

Usage: uv run python projects/li_2022_fca_10x/type_evidence.py
(needs .cache/fbbt.obo: curl -sL -o .cache/fbbt.obo http://purl.obolibrary.org/obo/fbbt.obo)
"""
import collections
import json
import re
from pathlib import Path

REPO = str(Path(__file__).resolve().parents[2])
terms={}; cur=None
for line in open(f'{REPO}/.cache/fbbt.obo'):
    line=line.rstrip('\n')
    if line=='[Term]': cur={'syn':[], 'is_a':[], 'rel':[]}; continue
    if line.startswith('[') : cur=None; continue
    if cur is None or ':' not in line: continue
    k,v=line.split(': ',1) if ': ' in line else (line,'')
    if k=='id': terms[v]=cur; cur['id']=v
    elif k=='name': cur['name']=v
    elif k=='def': cur['def']=re.match(r'"((?:[^"\\]|\\.)*)"',v).group(1)
    elif k=='synonym': 
        m=re.match(r'"((?:[^"\\]|\\.)*)" (\w+)',v); cur['syn'].append((m.group(1),m.group(2)))
    elif k=='is_a': cur['is_a'].append(v.split()[0])
    elif k=='relationship': cur['rel'].append(v.split()[:2])
    elif k=='is_obsolete': cur['obsolete']=v=='true'
    elif k=='replaced_by': cur['replaced_by']=v
    elif k=='consider': cur.setdefault('consider',[]).append(v)
def ancestors(t):
    seen=set(); st=[t]
    while st:
        x=st.pop()
        for p in terms.get(x,{}).get('is_a',[]):
            if p not in seen: seen.add(p); st.append(p)
    return seen
CELL='FBbt:00007002'
by_name=collections.defaultdict(set)
for i,t in terms.items():
    if t.get('obsolete') or 'name' not in t: continue
    by_name[t['name'].lower()].add(i)
    for s,sc in t['syn']:
        if sc=='EXACT': by_name[s.lower()].add(i)
anns={}
for proj in ('10x','ss2'):
    for a in json.load(open(f'{REPO}/projects/li_2022_fca_{proj}/cell_type_annotations.json'))['annotations']:
        if a.get('unannotated'): continue
        d=anns.setdefault(a['type'],{'type':a['type'],'author_ids':set(),'broad':collections.Counter(),'where':collections.Counter()})
        if a.get('author_ontology_id'): d['author_ids'].add(a['author_ontology_id'])
        if a.get('author_broad'): d['broad'][a['author_broad']]+=a['cell_number']
        d['where'][f"{proj}:{a['clustering']}"]+=a['cell_number']
out=[]
for typ,d in sorted(anns.items()):
    ids=sorted({x for s in d['author_ids'] for x in s.split('; ')})
    info=[]
    for i in ids:
        if not i.startswith('FBbt'): info.append({'id':i}); continue
        t=terms.get(i,{})
        info.append({'id':i,'name':t.get('name'),'definition':t.get('def'),'obsolete':t.get('obsolete',False),'replaced_by':t.get('replaced_by'),
                     'is_cell': CELL in ancestors(i) or i==CELL})
    cands=set()
    for i in info:
        n=i.get('name')
        if n and not n.startswith('adult '):
            cands |= {('adult variant',x) for x in by_name.get('adult '+n.lower(),())}
        if i.get('replaced_by'): cands.add(('replaced_by',i['replaced_by']))
    t2=typ.rstrip('*').lower()
    cands |= {('label match',x) for x in by_name.get(t2,()) if x not in ids}
    cands |= {('adult label match',x) for x in by_name.get('adult '+t2,()) if x not in ids}
    out.append({'type':typ,'author':info,'broad':dict(d['broad']),'where':dict(d['where']),
                'candidates':[{'why':w,'id':x,'name':terms[x]['name'],'definition':terms[x].get('def')} for w,x in sorted(cands)]})
version=next(l.split(': ',1)[1].strip() for l in open(f'{REPO}/.cache/fbbt.obo') if l.startswith('data-version'))
Path(REPO,'projects/li_2022_fca_10x/type_evidence.json').write_text(json.dumps(
    {'fbbt_version':version,'types':out},indent=2,ensure_ascii=False)+'\n')
# summary
c=collections.Counter()
for o in out:
    a=o['author']
    if not a or a[0]['id'] in ('Manual Annotation',): c['manual/none']+=1
    elif len(a)>1: c['multi']+=1
    elif a[0].get('obsolete'): c['obsolete']+=1
    elif not a[0].get('is_cell'): c['author term not a cell type']+=1
    else: c['single cell term']+=1
print(len(out),'types',dict(c)); print('with candidates',sum(bool(o['candidates']) for o in out))
