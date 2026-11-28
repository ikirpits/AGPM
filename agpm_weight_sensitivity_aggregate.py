"""
Random and extreme criterion-weight sensitivity of the AGPM results.

Usage
    python agpm_weight_sensitivity_aggregate.py [agpm_method_results.csv]

Needs: pandas, numpy, scipy

Reads the public criterion means per method (agpm_method_results.csv, no rater-level data needed; for
Waterfall and Scrum, rated in both groups, the means are the mean of the group means), draws 10,000 random weight sets per axis from a
flat Dirichlet distribution (seed 2026) and reports the stability of the gap, ranking and quadrants.
Also evaluates the 25 combinations with all weight on one criterion per axis.
Gives the same results as agpm_weight_sensitivity.py run on the restricted rater-level workbook.
Writes agpm_weight_sensitivity_results.json next to the input file.
"""
import sys, json
import numpy as np
from scipy.stats import spearmanr, wilcoxon
from pathlib import Path
import pandas as pd
src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("agpm_method_results.csv")
cm = pd.read_csv(src).set_index("method")
M = sorted(cm.index)
A = cm.loc[M, ["A1", "A2", "A3", "A4", "A5"]].to_numpy()
G = cm.loc[M, ["G1", "G2", "G3", "G4", "G5"]].to_numpy()
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
json.dump(dict(res=res,per=per,ex=[float(ex[:,0].min()),float(np.median(ex[:,0])),int(ex[:,1].max()),float(ex[:,2].min()),float(ex[:,2].max()),float(ex[:,3].max())]),open(src.with_name('agpm_weight_sensitivity_results.json'),'w'))
