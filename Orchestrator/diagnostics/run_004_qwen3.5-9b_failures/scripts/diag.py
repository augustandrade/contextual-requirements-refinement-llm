import os, sys, itertools, json, time, urllib.request
os.environ['OLLAMA_MODEL']='qwen3.5:9b'
sys.path.insert(0,'.')
from pathlib import Path
import agents, process_corpus as pc
SP=Path("/private/tmp/claude-501/-Users-augustandrade-Library-Mobile-Documents-com-apple-CloudDocs----ARQUIVOS----ACADEMICO----MBA-USP-TCC/8e0639f7-068c-480e-8f50-57561b720b31/scratchpad")
n=itertools.count(1)
LOG=SP/'raw6000'/'diag_log.txt'
def call(system_prompt,user_content,timeout=None,num_ctx=2048,num_predict=1500):
    # Diagnostico: mesmo pedido do pipeline, mas com num_predict elevado a 6000
    np_=6000 if num_predict>=2500 else num_predict
    payload=json.dumps({'model':'qwen3.5:9b','messages':[{'role':'system','content':system_prompt},{'role':'user','content':user_content}],
      'stream':False,'think':False,'options':{'temperature':0.0,'num_ctx':num_ctx,'num_predict':np_}}).encode()
    req=urllib.request.Request('http://localhost:11434/api/chat',data=payload,headers={'Content-Type':'application/json'},method='POST')
    t=time.time()
    with urllib.request.urlopen(req,timeout=1800) as r: d=json.loads(r.read().decode())
    i=next(n); raw=d['message']['content']
    (SP/'raw6000'/f'call{i:02d}.txt').write_text(raw,encoding='utf-8')
    with open(LOG,'a') as f: f.write(f"call{i:02d} num_predict={np_} done_reason={d.get('done_reason')} eval_count={d.get('eval_count')} prompt_eval_count={d.get('prompt_eval_count')} secs={time.time()-t:.0f}\n")
    return raw
agents._call_model_ollama=call
run_dir=SP/'run_copy2'
m=pc.load_yaml(pc.MANIFEST)
for it in m['items']:
    b=it['file'].split('/')[-1][:6]
    if b in ('REQ-05','REQ-13'):
        pc.process_item(it, run_dir, contexts={'REQ-05':['C2'],'REQ-13':['C2','C3']}[b])
