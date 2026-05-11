import json
with open('/home/xp/hermes-study-space/data/research.json') as f:
    data = json.load(f)
p2 = [p for p in data['phases'] if p['day']==2][0]
print('Status:', p2['status'])
print('Sections:', len(p2['sections']))
print('Reflections:', len(p2['reflections']))
for s in p2['sections']:
    print(f'  - {s["heading"]}')
print()
print('Summary preview:', p2['summary'][:300])
