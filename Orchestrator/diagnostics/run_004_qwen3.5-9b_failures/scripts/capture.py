import os, sys, itertools
os.environ['OLLAMA_MODEL']='qwen3.5:9b'
sys.path.insert(0,'.')
from pathlib import Path
import agents, process_corpus as pc
SP=Path("/private/tmp/claude-501/-Users-augustandrade-Library-Mobile-Documents-com-apple-CloudDocs----ARQUIVOS----ACADEMICO----MBA-USP-TCC/8e0639f7-068c-480e-8f50-57561b720b31/scratchpad")
n=itertools.count(1)
orig=agents._call_model_ollama
def rec(system_prompt,user_content,*a,**k):
    raw=orig(system_prompt,user_content,*a,**k)
    i=next(n)
    (SP/'raw'/f'call{i:02d}.txt').write_text('### USER\n'+user_content[:300]+'\n### RAW\n'+raw,encoding='utf-8')
    return raw
agents._call_model_ollama=rec
run_dir=SP/'run_copy'
m=pc.load_yaml(pc.MANIFEST)
for it in m['items']:
    if it['file'].split('/')[-1].startswith(('REQ-05','REQ-13')):
        # force pending only failing ctx
        ctxs={'REQ-05':['C2'],'REQ-13':['C2','C3']}[it['file'].split('/')[-1][:6]]
        pc.process_item(it, run_dir, contexts=ctxs)
