"""Independent check of the AGPM bootstrap (Google Sheet, tab 3 Bootstrap).
Usage: python agpm_verify.py AGPM_dataset_anonymized.xlsx [seed]
Re-computes GABS 95% limits and lower and upper percentile rank (2.5th and 97.5th) from the ratings (raters resampled with
replacement within each group, both sessions kept together, 5,000 resamples) and prints the
difference from the values in the Sheet (SHEET below, taken from tabs 3 and 4 after the recalculation of 25/11/2026 (Code.gs, seed 2026)).
Differences of a few thousandths are expected: the random number generators differ."""
import numpy as np, pandas as pd, sys
from scipy.stats import rankdata
SRC=sys.argv[1]
T3="""SAFe 1 1 3,781 4,02
DevOps 2 2 3,653 3,88
KIBO 3 4 3,479 3,693
DSDM 3 5 3,358 3,558
PRINCE2_Agile 4 6 3,278 3,548
DAD 5 8 3,103 3,376
XP 6 9 2,918 3,284
Scrum 6 9 2,996 3,224
UP/RUP 7 9 2,952 3,115
MSF 10 14 2,653 2,901
LeSS 10 15 2,59 2,861
FDD 10 13 2,67 2,898
AUP 12 16 2,508 2,801
Kanban 10 14 2,637 2,922
Spiral 12 17 2,365 2,731
ASD 14 17 2,336 2,676
Scrumban 17 19 2,029 2,546
Crystal 15 19 2,269 2,54
V-Model 17 19 2,151 2,516
Waterfall 20 20 1,813 2,022"""
T4="""SAFe 3,6 3,87 3,92 4,24
DevOps 4,42 4,71 3,04 3,37
KIBO 3,66 3,89 3,27 3,56
DSDM 3,35 3,6 3,3 3,58
PRINCE2_Agile 3,2 3,5 3,28 3,67
DAD 3,68 3,96 2,64 3
XP 3,96 4,2 2,26 2,74
Scrum 3,86 4,06 2,42 2,7
UP/RUP 2,78 3,06 3,05 3,27
MSF 2,46 2,79 2,81 3,08
LeSS 3,73 4,01 1,95 2,25
FDD 3,01 3,25 2,35 2,66
AUP 3,34 3,58 1,97 2,35
Kanban 4,01 4,36 1,93 2,24
Spiral 3,12 3,46 1,87 2,3
ASD 3,18 3,44 1,81 2,24
Scrumban 3,71 4,03 1,38 1,88
Crystal 3,08 3,35 1,76 2,08
V-Model 1,83 2,27 2,49 2,95
Waterfall 1,42 1,62 2,42 2,78"""
f=lambda s:float(s.replace(',','.'))
V={}
for l in T3.splitlines():
    p=l.split(); V[p[0].replace('_',' ')]=dict(rf=int(p[1]),rt=int(p[2]),gl=f(p[3]),gh=f(p[4]))
for l in T4.splitlines():
    p=l.split(); V[p[0].replace('_',' ')].update(xl=f(p[1]),xh=f(p[2]),yl=f(p[3]),yh=f(p[4]))

L=pd.read_excel(SRC,'Ratings_long')
methods=sorted(L.method.unique()); mi={m:i for i,m in enumerate(methods)}
crits=[f'A{i}' for i in range(1,6)]+[f'G{i}' for i in range(1,6)]; ci={c:i for i,c in enumerate(crits)}
grp={}
for g,d in L.groupby('group'):
    raters=sorted(d.rater_id.unique()); ri={r:i for i,r in enumerate(raters)}
    M=np.full((len(raters),20,10),np.nan)
    for r,m,c,v in zip(d.rater_id,d.method,d.criterion,d.score): M[ri[r],mi[m],ci[c]]=v
    grp[g]=M
inG={m:[g for g in grp if (~np.isnan(grp[g][:,mi[m],:])).any()] for m in methods}
def xy_from(W):  # W: dict g -> weights per rater
    X=np.zeros(20);Y=np.zeros(20)
    for m in methods:
        xs=[];ys=[]
        for g in inG[m]:
            M=grp[g][:,mi[m],:]; Z=np.nan_to_num(M); K=~np.isnan(M)
            w=W[g]
            xs.append((w@Z[:,:5]).sum()/(w@K[:,:5]).sum()); ys.append((w@Z[:,5:]).sum()/(w@K[:,5:]).sum())
        X[mi[m]]=np.mean(xs);Y[mi[m]]=np.mean(ys)
    return X,Y
ones={g:np.ones(grp[g].shape[0]) for g in grp}
X0,Y0=xy_from(ones); G0=2*X0*Y0/(X0+Y0)
rng=np.random.default_rng(int(sys.argv[2]) if len(sys.argv)>2 else 1)
B=5000; GB=np.zeros((B,20)); RK=np.zeros((B,20)); XB=np.zeros((B,20)); YB=np.zeros((B,20))
for b in range(B):
    W={g:np.bincount(rng.integers(0,n,n),minlength=n).astype(float) for g,n in ((g,grp[g].shape[0]) for g in grp)}
    X,Y=xy_from(W); XB[b]=X; YB[b]=Y; GB[b]=2*X*Y/(X+Y); RK[b]=rankdata(-GB[b],method='average')
gl,gh=np.percentile(GB,[2.5,97.5],axis=0); rl,rh=np.percentile(RK,[2.5,97.5],axis=0)
rows=[]
for m in methods:
    i=mi[m]; v=V[m]
    rows.append((m,round(G0[i],3),round(gl[i],3),v['gl'],round(gh[i],3),v['gh'],round(rl[i]),v['rf'],round(rh[i]),v['rt']))
df=pd.DataFrame(rows,columns=['method','GABS','py_lo','sheet_lo','py_hi','sheet_hi','py_rlo','sheet_rlo','py_rhi','sheet_rhi'])
df['d_lo']=(df.py_lo-df.sheet_lo).round(3); df['d_hi']=(df.py_hi-df.sheet_hi).round(3)
print(df.to_string()); print('max |d| lo/hi',df.d_lo.abs().max(),df.d_hi.abs().max(),'rank mismatches',(df.py_rlo!=df.sheet_rlo).sum(),(df.py_rhi!=df.sheet_rhi).sum())


# X and Y intervals (2.5th and 97.5th percentiles) compared with the Sheet values
xl,xh=np.percentile(XB,[2.5,97.5],axis=0); yl,yh=np.percentile(YB,[2.5,97.5],axis=0)
rows=[]
for m in methods:
    i=mi[m]; v=V[m]
    rows.append((m,round(xl[i],3),v['xl'],round(xh[i],3),v['xh'],round(yl[i],3),v['yl'],round(yh[i],3),v['yh']))
dx=pd.DataFrame(rows,columns=['method','py_Xlo','sheet_Xlo','py_Xhi','sheet_Xhi','py_Ylo','sheet_Ylo','py_Yhi','sheet_Yhi'])
for a,b in (('Xlo','Xlo'),('Xhi','Xhi'),('Ylo','Ylo'),('Yhi','Yhi')): dx['d_'+a]=(dx['py_'+a]-dx['sheet_'+b]).round(3)
print(); print(dx.to_string())
print('max |d| X lo/hi',dx.d_Xlo.abs().max(),dx.d_Xhi.abs().max(),'Y lo/hi',dx.d_Ylo.abs().max(),dx.d_Yhi.abs().max())
# Quadrant probabilities over the same resamples (threshold 3.0 on both axes, as in the manuscript)
def quad(x,y):
    return np.where((x>=3)&(np.round(y,9)>=3),'Integrated Leaders',np.where(x>=3,'Agile-First',np.where(np.round(y,9)>=3,'Governance-Heavy','Baseline')))
Q=quad(XB,YB); names=['Integrated Leaders','Agile-First','Governance-Heavy','Baseline']
base=quad(X0,Y0)
qp=pd.DataFrame({'method':methods,'point_quadrant':[base[mi[m]] for m in methods],'X':X0.round(4),'Y':Y0.round(4)})
for q in names: qp['P('+q+')']=[round(float((Q[:,mi[m]]==q).mean()),4) for m in methods]
qp['P(point quadrant)']=[round(float((Q[:,mi[m]]==base[mi[m]]).mean()),4) for m in methods]
print(); print(qp.to_string(index=False))
qp.to_csv('agpm_quadrant_probabilities.csv',index=False)
print('written agpm_quadrant_probabilities.csv (seed',int(sys.argv[2]) if len(sys.argv)>2 else 1,')')
