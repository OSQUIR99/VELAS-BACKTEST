import sys,os,glob,time
sys.path.insert(0,'/home/claude/velas-backtest/MOTOR')
import pandas as pd, numpy as np
# duplicate ids across all candidate folders
dirs=['/home/claude/mej/gh','/home/claude/velas-backtest/MOTOR/listas','/home/claude/velas-backtest/MOTOR/listas_reconstruidas','/home/claude/velas-backtest/MOTOR/listas_reconstruidas/referencia','/home/claude/velas-backtest/MOTOR/listas/referencia']
for d in dirs:
    print('==',d)
    ids={}
    for p in sorted(glob.glob(d+'/*.parquet')):
        if p.endswith('_diario.parquet'): continue
        o=pd.read_parquet(p); n=os.path.basename(p)[:-8]
        i=o['id'].astype(str) if 'id' in o else pd.Series([f'{n}_{k}' for k in range(len(o))])
        print(f'  {n:40s} n={len(o):6d} uniq={i.nunique()} real={os.path.realpath(p).split("velas-backtest/")[-1]}')
        ids[n]=set(i)
    ks=list(ids)
    for a in range(len(ks)):
        for b in range(a+1,len(ks)):
            c=len(ids[ks[a]]&ids[ks[b]])
            if c: print('  SOLAPE',ks[a],ks[b],c)
