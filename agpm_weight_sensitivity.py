import numpy as np, json
from scipy.stats import spearmanr, wilcoxon
# method: (nA_ax,nB_ax,nA_g,nB_g, sumsA_a,sumsB_a,sumsA_g,sumsB_g)
Z=[0]*5
D={
'ASD':(43,0,34,0,[127,162,109,153,160],Z,[70,81,81,50,59],Z),
'AUP':(0,45,0,39,Z,[164,140,140,182,153],Z,[101,69,81,62,108]),
'Crystal':(0,45,0,39,Z,[140,141,137,154,151],Z,[85,94,80,49,66]),
'DAD':(0,45,0,39,Z,[161,169,175,198,156],Z,[96,130,126,123,75]),
'DSDM':(0,45,0,39,Z,[157,158,158,145,164],Z,[133,168,138,108,125]),
'DevOps':(43,0,34,0,[192,199,200,187,206],Z,[97,63,140,90,153],Z),
'FDD':(0,45,0,39,Z,[148,135,164,120,137],Z,[99,122,112,53,101]),
'KIBO':(43,0,34,0,[165,157,173,142,176],Z,[97,110,111,122,140],Z),
'Kanban':(0,45,0,39,Z,[187,189,192,202,173],Z,[107,96,89,50,63]),
'LeSS':(0,45,0,39,Z,[167,173,177,188,167],Z,[89,113,99,47,62]),
'MSF':(0,45,0,39,Z,[115,120,124,113,118],Z,[143,102,148,62,119]),
'PRINCE2 Agile':(43,0,34,0,[134,145,143,144,153],Z,[113,140,152,56,128],Z),
'SAFe':(43,0,34,0,[162,161,166,144,169],Z,[134,148,132,147,133],Z),
'Scrum':(43,45,34,39,[175,170,168,178,171],[172,169,175,189,175],[93,99,107,71,60],[97,130,119,82,74]),
'Scrumban':(43,0,34,0,[144,182,160,198,148],Z,[62,54,57,45,55],Z),
'Spiral':(43,0,34,0,[133,146,106,164,159],Z,[76,52,107,54,63],Z),
'UP/RUP':(0,45,0,39,Z,[149,117,129,100,163],Z,[156,126,146,60,128]),
'V-Model':(43,0,34,0,[76,81,77,99,107],Z,[106,85,112,77,79],Z),
'Waterfall':(43,45,34,39,[59,79,55,59,76],[70,76,55,54,85],[79,86,123,54,92],[86,106,142,60,120]),
'XP':(43,0,34,0,[169,167,177,183,181],Z,[82,96,92,48,106],Z)}
M=sorted(D)
def cm(nA,nB,sA,sB):
    out=[]
    for i in range(5):
        p=[]
        if nA: p.append(sA[i]/nA)
        if nB: p.append(sB[i]/nB)
        out.append(sum(p)/len(p))
    return out
A=np.array([cm(D[m][0],D[m][1],D[m][4],D[m][5]) for m in M])
G=np.array([cm(D[m][2],D[m][3],D[m][6],D[m][7]) for m in M])
json.dump({'M':M,'A':A.tolist(),'G':G.tolist()},open('crit.json','w'))
def run(w,v):
    X=A@w; Y=G@v; g=2*X*Y/(X+Y); return X,Y,g
def quad(X,Y,t=3.0): return np.where(X>=t,np.where(Y>=t,0,1),np.where(Y>=t,2,3))
w0=np.ones(5)/5
X0,Y0,g0=run(w0,w0)
print('mean X',X0.mean(),'mean Y',Y0.mean(),'gap',(Y0-X0).mean())
for m,x,y in zip(M,X0,Y0):
    if m in('SAFe','Waterfall','KIBO','DevOps'): print(m,round(x,3),round(y,3))
q0=quad(X0,Y0)
rank0=(-g0).argsort().argsort()+1
top0=set(np.argsort(-g0)[:3])
def wilc_p(X,Y):
    return wilcoxon(X-Y,method='exact').pvalue if len(set(np.round(X-Y,12)))==len(X) else wilcoxon(X-Y).pvalue
rng=np.random.default_rng(2026)
N=10000
rho=[];top3=[];safe1=[];kibo3=[];nq=[];gap=[];nlow=[];pw=[];qs=np.zeros((len(M),4));rk=np.zeros((N,len(M)))
for i in range(N):
    w=rng.dirichlet(np.ones(5)); v=rng.dirichlet(np.ones(5))
    X,Y,g=run(w,v)
    rho.append(spearmanr(g,g0)[0]); order=np.argsort(-g)
    top3.append(set(order[:3])==top0); safe1.append(M[order[0]]=='SAFe'); kibo3.append('KIBO' in [M[j] for j in order[:3]])
    q=quad(X,Y); nq.append(int((q!=q0).sum())); gap.append((Y-X).mean()); nlow.append(int((Y<X).sum()))
    pw.append(wilc_p(X,Y)); rk[i]=(-g).argsort().argsort()+1
    for j in range(len(M)): qs[j,q[j]]+=1
rho=np.array(rho)
res=dict(rho_med=float(np.median(rho)),rho_p5=float(np.percentile(rho,5)),rho_min=float(rho.min()),top3=float(np.mean(top3)),safe1=float(np.mean(safe1)),kibo3=float(np.mean(kibo3)),
 nq_med=float(np.median(nq)),nq_p95=float(np.percentile(nq,95)),nq_max=int(max(nq)),nq0=float(np.mean(np.array(nq)==0)),
 gap_med=float(np.median(gap)),gap_p5=float(np.percentile(gap,5)),gap_p95=float(np.percentile(gap,95)),gap_max=float(max(gap)),
 nlow_min=int(min(nlow)),nlow_med=float(np.median(nlow)),p_max=float(max(pw)),p_med=float(np.median(pw)),p_sig=float(np.mean(np.array(pw)<0.05)))
print(res)
per=[]
for j,m in enumerate(M):
    per.append([m,int(np.percentile(rk[:,j],5)),int(np.median(rk[:,j])),int(np.percentile(rk[:,j],95)),int(rank0[j]),round(100*qs[j,q0[j]]/N)])
for p in per: print(p)
# extreme single-criterion weights
ex=[]
for i in range(5):
    for k in range(5):
        w=np.zeros(5);w[i]=1;v=np.zeros(5);v[k]=1
        X,Y,g=run(w,v); ex.append((spearmanr(g,g0)[0],int((quad(X,Y)!=q0).sum()),M[np.argmax(g)],(Y-X).mean(),float(wilc_p(X,Y))))
ex=np.array([(e[0],e[1],e[3],e[4]) for e in ex]); 
print('extreme rho min/med',ex[:,0].min(),np.median(ex[:,0]),'nq max',ex[:,1].max(),'gap range',ex[:,2].min(),ex[:,2].max(),'p max',ex[:,3].max())
print('top by extreme:',sorted(set(e for e in [M[np.argmax(run(np.eye(5)[i],np.eye(5)[k])[2])] for i in range(5) for k in range(5)])))
json.dump(dict(res=res,per=per,ex=[float(ex[:,0].min()),float(np.median(ex[:,0])),int(ex[:,1].max()),float(ex[:,2].min()),float(ex[:,2].max()),float(ex[:,3].max())]),open('wres.json','w'))
