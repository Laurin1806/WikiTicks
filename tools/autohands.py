import math,numpy as np
def ray_profile(L,hub,ang,d0,d1,thr):
    h,w=L.shape;t=math.radians(ang);ax,ay=math.sin(t),-math.cos(t);px,py=math.cos(t),math.sin(t);out=[]
    for d in range(d0,d1):
        cx,cy=hub[0]+d*ax,hub[1]+d*ay;br=[]
        for s in range(-40,41):
            x,y=int(round(cx+s*px)),int(round(cy+s*py))
            if 0<=x<w and 0<=y<h and L[y,x]>=thr: br.append(s)
        # zusammenhängenden Block um s≈0 nehmen
        if not br or min(abs(b) for b in br)>6: out.append(None);continue
        s0=min(br,key=abs);lo=hi=s0;S=set(br)
        while lo-1 in S or lo-2 in S: lo-=1 if lo-1 in S else 2
        while hi+1 in S or hi+2 in S: hi+=1 if hi+1 in S else 2
        out.append((lo,hi))
    return out
def find_dirs(L,hub,R,thr):
    h,w=L.shape;sc=[]
    for a10 in range(0,3600,5):
        a=a10/10;t=math.radians(a);v=0;n=0
        for d in range(int(R*.18),int(R*.42)):
            x,y=int(round(hub[0]+d*math.sin(t))),int(round(hub[1]-d*math.cos(t)))
            if 0<=x<w and 0<=y<h: v+=L[y,x]>=thr;n+=1
        sc.append((a,v/max(n,1)))
    arr=np.array([s for _,s in sc]);peaks=[]
    for i in range(len(arr)):
        if arr[i]>.55 and arr[i]>=arr[i-1] and arr[i]>=arr[(i+1)%len(arr)]:
            # Plateau-Mitte
            j=i
            while arr[(j+1)%len(arr)]==arr[i] and j-i<40: j+=1
            peaks.append(((sc[i][0]+sc[j%len(arr)][0])/2,arr[i]))
    # zusammenfassen (<4° Abstand)
    out=[]
    for a,s in sorted(peaks):
        if out and abs(a-out[-1][0])<4: 
            if s>out[-1][1]: out[-1]=(a,s)
        else: out.append((a,s))
    return out
def refine(L,hub,ang,R,thr):
    best=(ang,-1)
    for da in np.arange(-3,3.01,.25):
        prof=ray_profile(L,hub,ang+da,int(R*.2),int(R*.6),thr)
        sym=[-abs(p[0]+p[1]) for p in prof if p]
        score=len(sym)*100+sum(sym)
        if score>best[1]: best=(ang+da,score)
    return best[0]
def analyse(L,hub,a,R,thr):
    prof=ray_profile(L,hub,a,6,int(R*1.02),thr)
    ws=[(d+6,p) for d,p in enumerate(prof) if p]
    if not ws: return None
    last=ws[0][0];seq=[]
    for d,p in ws:
        if d-last>4 and d>R*.25: break
        seq.append((d,p));last=d
    widths=np.array([p[1]-p[0]+1 for d,p in seq]);return seq,float(np.median(widths)),seq[-1][0]
def hand_shapes(L,hub,R,thr=150,inset=.28,minw=6,mercedes=True,second=True,log=None,hour_style=None):
    dirs=find_dirs(L,hub,R,thr);cand=[]
    for a,s in dirs:
        a=refine(L,hub,a,R,thr);r=analyse(L,hub,a,R,thr)
        if not r: continue
        seq,med,dmax=r
        if any(abs(((a-c[0])+180)%360-180)<5 for c in cand): continue
        cand.append((a,seq,med,dmax))
    mains=sorted([c for c in cand if c[2]>=minw and c[3]>R*.45],key=lambda c:-c[3])
    secs=sorted([c for c in cand if c[2]<minw],key=lambda c:-c[3])
    shapes=[];info=[];hands=[]
    if mains: hands.append(('min',mains[0]))
    if len(mains)>1: hands.append(('hour',mains[1]))
    if secs and second: hands.append(('sec',secs[0]))
    for role,(a,seq,med,dmax) in hands:
        t=math.radians(a);info.append((round(a,1),role,int(med),dmax))
        if role=='sec':
            wide=[(d,p) for d,p in seq if p[1]-p[0]+1>=med*2.4 and d>R*.25]
            if wide:
                c=np.mean([d for d,_ in wide]);rad=(max(p[1]-p[0] for _,p in wide)+1)/2*.72
                shapes.append({'t':'circle','c':[hub[0]+c*math.sin(t),hub[1]-c*math.cos(t)],'r':rad})
            continue
        circ=[(d,p) for d,p in seq if p[1]-p[0]+1>med*1.7 and d>R*.25]
        if role=='min':
            # Verbreiterung am Ende = darunterliegender Index
            if circ and circ[0][0]>dmax*.8:
                cd=(circ[0][0]+circ[-1][0])/2;cr=max(p[1]-p[0]+1 for _,p in circ)/2
                shapes.append({'t':'circle','c':[hub[0]+cd*math.sin(t),hub[1]-cd*math.cos(t)],'r':cr*.95,'under':True})
                endd=circ[0][0]-2
            else: endd=dmax
            body=[(d,p) for d,p in seq if dmax*.22<d<=endd]
        elif mercedes and circ:
            # Kreis: Ausdehnung entlang der Achse über Breite > 1.25*Median bestimmen
            circ2=[(d,p) for d,p in seq if p[1]-p[0]+1>med*1.25 and d>R*.25]
            dc0,dc1=circ2[0][0],circ2[-1][0];cr=max(p[1]-p[0]+1 for _,p in circ)/2;cd=(dc0+dc1)/2
            ex,ey=hub[0]+cd*math.sin(t),hub[1]-cd*math.cos(t);B=L>=thr;best=(-1e9,ex,ey);H,W=L.shape
            yy,xx=np.mgrid[-int(cr)-8:int(cr)+9,-int(cr)-8:int(cr)+9];rr=np.hypot(xx,yy);din=rr<=cr*.92;ring=(rr>cr+1.5)&(rr<cr+5)
            for oy in np.arange(-8,8.5,1):
                for ox in np.arange(-8,8.5,1):
                    cx_,cy_=int(round(ex+ox)),int(round(ey+oy));y0=cy_-int(cr)-8;x0=cx_-int(cr)-8
                    if y0<0 or x0<0 or y0+rr.shape[0]>H or x0+rr.shape[1]>W: continue
                    win=B[y0:y0+rr.shape[0],x0:x0+rr.shape[1]];sc=win[din].mean()-win[ring].mean()
                    if sc>best[0]: best=(sc,cx_,cy_)
            shapes.append({'t':'merc','c':[best[1],best[2]],'r1':cr*.8,'sp':[a+60,a+180,a-60],'sw':max(1.6,cr*.12)})
            body=[(d,p) for d,p in seq if d>dc1+3]
            body=body[:max(4,int(len(body)*.82))]
            if len(body)<4: continue
            ww=[[d,max(0,(p[1]-p[0]+1)*(1-2*inset))] for d,p in body];ww[-1][1]=0
            off=float(np.mean([(p[0]+p[1])/2 for _,p in body]))
            shapes.append({'t':'sword','ang':a,'off':off,'w':ww[::max(1,len(ww)//8)]+[ww[-1]]});continue
        else:
            body=[(d,p) for d,p in seq if d>dmax*.22]
        if len(body)<5: continue
        ww=[];offs=[]
        for d,p in body:
            wd=p[1]-p[0]+1;ww.append([d,max(0,wd*(1-2*inset))]);offs.append((p[0]+p[1])/2)
        ww[0][1]*=.6;ww[-1][1]=0
        if len(ww)>3: ww[-2][1]*=.5
        shapes.append({'t':'sword','ang':a,'off':float(np.median(offs)),'w':ww[::max(1,len(ww)//10)]+[ww[-1]]})
    if log is not None: log.extend(info)
    return shapes,dirs
