import pickle
from tvlib import tvohlc
D=pickle.load(open('datos.pkl','rb'))
for k in ['CLSK','WULF','HUT','CIFR','IREN','CORZ','BITF','MSTR','MARA','RIOT']:
    try:
        x=tvohlc('NASDAQ:'+k,'1D'); D[k]=x if k not in D else D[k]
        h=tvohlc('NASDAQ:'+k,'60',6000); D[k+'_h']=h; print(k,len(x),x.index[0].date(),'| 1h',len(h),h.index[0])
    except Exception as e: print(k,'ERR',e)
pickle.dump(D,open('datos.pkl','wb'))
