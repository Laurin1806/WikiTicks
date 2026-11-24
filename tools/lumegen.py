"""Leuchtebene je Uhr: helle Flächen (Indizes, Zeiger) innerhalb des Zifferblatts, Ausschlüsse je Uhr."""
import json,sys,math,numpy as np
from PIL import Image,ImageFilter
from collections import deque
ROOT='/home/user/WikiTicks/'
def comps(mask):
    h,w=mask.shape;lab=np.zeros((h,w),np.int32);out=[];n=0
    ys,xs=np.nonzero(mask)
    for y0,x0 in zip(ys,xs):
        if lab[y0,x0]:continue
        n+=1;q=deque([(y0,x0)]);lab[y0,x0]=n;pts=[]
        while q:
            y,x=q.popleft();pts.append((y,x))
            for dy,dx in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                yy,xx=y+dy,x+dx
                if 0<=yy<h and 0<=xx<w and mask[yy,xx] and not lab[yy,xx]: lab[yy,xx]=n;q.append((yy,xx))
        out.append(np.array(pts))
    return out
def gen(img, spec):
    im=Image.open(ROOT+img).convert('RGB');a=np.array(im).astype(int);h,w,_=a.shape
    L=a.mean(2);S=a.max(2)-a.min(2)
    cx,cy,r=spec['c'][0]*w,spec['c'][1]*h,spec['r']*w
    yy,xx=np.mgrid[0:h,0:w];inside=np.hypot(xx-cx,yy-cy)<=r
    m=inside&(L>=spec.get('thr',175))&(S<=spec.get('sat',70))
    if spec.get('mode')=='light':  # helles Zifferblatt: nur von dunklen Rändern umschlossene helle Flächen (nicht die Zifferblattfläche)
        lm=(L>=spec.get('thr',175))&(S<=spec.get('sat',70))&~np.array([[False]])
        keepL=np.zeros((h,w),bool);mn=spec.get('min',.0002)*w*w;mx=spec.get('max',.004)*w*w
        for c in comps(lm&inside):
            if mn<=len(c)<=mx and not ((c[:,0]<=0)|(c[:,1]<=0)).any(): keepL[c[:,0],c[:,1]]=True
        for x0,y0,x1,y1 in spec.get('ex',[]): keepL[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=False
        m=keepL
    for x0,y0,x1,y1 in spec.get('ex',[]): m[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=False
    if 'exr' in spec:
        hx0,hy0=spec['hub'];rd=np.hypot(xx-hx0,yy-hy0);m&=~((rd>=spec['exr'][0])&(rd<=spec['exr'][1]))
    k=spec.get('open',0)
    if k: m=np.array(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k)))>127
    keep=np.zeros((h,w),bool);minA=spec.get('min',.0004)*w*w
    for c in comps(m):
        if len(c)<minA: continue
        y0,x0=c.min(0);y1,x1=c.max(0)
        sub=np.zeros((y1-y0+3,x1-x0+3),bool);sub[c[:,0]-y0+1,c[:,1]-x0+1]=True
        # Löcher füllen: alles, was vom Rand aus nicht erreichbar ist, gehört zur Fläche
        out=np.zeros_like(sub);q=deque([(0,0)]);out[0,0]=True;H2,W2=sub.shape
        while q:
            y,x=q.popleft()
            for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
                yy,xx=y+dy,x+dx
                if 0<=yy<H2 and 0<=xx<W2 and not sub[yy,xx] and not out[yy,xx]: out[yy,xx]=True;q.append((yy,xx))
        fill=~out
        if spec.get('maxA') and fill.sum()>spec['maxA']*w*w: continue   # sehr große helle Fläche (Hilfszifferblatt, Zifferblattausschnitt): keine Leuchtmasse
        if spec.get('nowin'):   # Datums-/Tagesfenster: fast rechteckig gefüllt, mit dunklen Ziffern darin
            bb=(y1-y0+1)*(x1-x0+1);fr=fill.sum()/bb;holes=(fill.sum()-len(c))/max(1,fill.sum())
            if fr>.84 and holes>.1 and .5<(x1-x0+1)/(y1-y0+1)<2.6: continue
        ys2,xs2=np.nonzero(fill);keep[ys2+y0-1,xs2+x0-1]=True
    # Zeiger: automatisch gefundene Flächen am Zeigerzentrum entfernen, Leuchtmasse stattdessen als Form zeichnen
    if 'hub' in spec:
        hx,hy=spec['hub'];hr=spec.get('hubr',14)
        lab_keep=keep.copy();handm=np.zeros((h,w),bool)
        if spec.get('hubcut',True):
          for c in comps(lab_keep):
            if (np.hypot(c[:,1]-hx,c[:,0]-hy)<hr).any(): keep[c[:,0],c[:,1]]=False
        # Zeigerfläche selbst (helle Pixel der entfernten Flächen, ohne Füllung) als Abdeckung merken
        hm=(L>=spec.get('thr',175))&(S<=spec.get('sat',70))
        for c in comps(hm&inside):
            if (np.hypot(c[:,1]-hx,c[:,0]-hy)<hr).any(): handm[c[:,0],c[:,1]]=True
    else: handm=np.zeros((h,w),bool)
    from PIL import ImageDraw
    lg=[]
    if spec.get('autohands'):
        import autohands
        lg=[];shs,_=autohands.hand_shapes(L,spec['hub'],spec.get('R',r),thr=spec.get('hthr',150),inset=spec.get('inset',.28),second=spec.get('sec',True),force=spec.get('force'),mercedes=spec.get('merc',True),nounder=spec.get('nounder',False),log=lg)
        shs=[f for f in shs if not (f['t']=='sword' and any(abs(((f['ang']-x)+180)%360-180)<5 for x in spec.get('skip',[])))]
        spec=dict(spec);spec['shapes']=shs+spec.get('shapes',[]);print('Zeiger',lg)
        # automatisch übernommene Flächen entlang der Zeigerachsen entfernen (Zeiger nur über die Leuchtformen)
        hx,hy=spec['hub']
        yy3,xx3=np.mgrid[0:h,0:w]
        for a_,kind,mw,dm in lg:
            t=math.radians(a_);ax_,ay_=math.sin(t),-math.cos(t)
            if kind=='sec':  # Sekundenzeiger: alles entlang des Zeigers löschen, nur der Leuchtpunkt kommt als Form
                dx3=xx3-hx;dy3=yy3-hy;al=dx3*ax_+dy3*ay_;pe=np.abs(-dx3*ay_+dy3*ax_)
                keep[(al>0)&(al<dm+8)&(pe<spec.get('secw',3.5))]=False
                ds=[math.hypot(c[:,1].mean()-hx,c[:,0].mean()-hy) for c in comps(keep.copy()) if len(c)>20]
                ds=[x for x in ds if x>spec.get('R',r)*.55]
                if ds:
                    Rr=float(np.median(ds))
                    for c in comps(keep.copy()):
                        dx4=c[:,1]-hx;dy4=c[:,0]-hy;al4=dx4*ax_+dy4*ay_;pe4=np.abs(-dx4*ay_+dy4*ax_)
                        if (pe4<4).any() and (al4.max()-al4.min())>1.6*(pe4.max()-pe4.min()+1) and abs(al4.mean()-Rr)<Rr*.25:
                            wd=pe4.max()+1;drop=al4<Rr-wd*1.15;keep[c[drop,0],c[drop,1]]=False
                continue
            for c in comps(keep.copy()):
                dx=c[:,1]-hx;dy=c[:,0]-hy;along=dx*ax_+dy*ay_;perp=np.abs(-dx*ay_+dy*ax_)
                if ((perp<max(mw,4)*.9)&(along>0)&(along<dm+6)).mean()>.5: keep[c[:,0],c[:,1]]=False
    shp=Image.new('L',(w*4,h*4),0);dr=ImageDraw.Draw(shp);S4=4
    shp2=Image.new('L',(w*4,h*4),0);dr2=ImageDraw.Draw(shp2)
    for f in spec.get('shapes',[]):
        if f['t']=='sword':  # Füllung entlang der Zeigerachse: Liste [Abstand, Breite]
            hx,hy=f.get('hub',spec.get('hub'));t=math.radians(f['ang']);ax,ay=math.sin(t),-math.cos(t);px,py=math.cos(t),math.sin(t);off=f.get('off',0)
            L1=[];L2=[]
            for d,wd in f['w']:
                cx_,cy_=hx+d*ax+off*px,hy+d*ay+off*py;L1.append(((cx_+wd/2*px)*S4,(cy_+wd/2*py)*S4));L2.append(((cx_-wd/2*px)*S4,(cy_-wd/2*py)*S4))
            dr.polygon(L1+L2[::-1],fill=255)
        elif f['t']=='merc':  # Mercedes-Kreis: Kreisfläche ohne Speichen
            cx_,cy_=f['c'];r1=f['r1'];r0=f.get('r0',0)
            dr.ellipse([(cx_-r1)*S4,(cy_-r1)*S4,(cx_+r1)*S4,(cy_+r1)*S4],fill=255)
            if r0: dr.ellipse([(cx_-r0)*S4,(cy_-r0)*S4,(cx_+r0)*S4,(cy_+r0)*S4],fill=0)
            for sp in f['sp']:
                t=math.radians(sp);ax,ay=math.sin(t),-math.cos(t);px,py=math.cos(t),math.sin(t);sw=f.get('sw',2)
                pts=[(cx_+sw*px,cy_+sw*py),(cx_+sw*px+(r1+2)*ax,cy_+sw*py+(r1+2)*ay),(cx_-sw*px+(r1+2)*ax,cy_-sw*py+(r1+2)*ay),(cx_-sw*px,cy_-sw*py)]
                dr.polygon([(x*S4,y*S4) for x,y in pts],fill=0)
        elif f['t']=='idx':  # Balkenindizes an festen Winkeln (Mitte im Abstand r vom Zeigerzentrum)
            hx_,hy_=f.get('hub',spec.get('hub'))
            for A in f['angs']:
                t=math.radians(A);ax,ay=math.sin(t),-math.cos(t);px,py=math.cos(t),math.sin(t);cx_,cy_=hx_+f['r']*ax,hy_+f['r']*ay;Lh,Wh=f['L']/2,f['W']/2
                pts=[(cx_+u*ax+v*px,cy_+u*ay+v*py) for u,v in((-Lh,-Wh),(Lh,-Wh),(Lh,Wh),(-Lh,Wh))]
                dr.polygon([(x*S4,y*S4) for x,y in pts],fill=255)
        elif f['t']=='circle':
            cx_,cy_=f['c'];r1=f['r']
            if f.get('under'): dr2.ellipse([(cx_-r1)*S4,(cy_-r1)*S4,(cx_+r1)*S4,(cy_+r1)*S4],fill=255)
            else: dr.ellipse([(cx_-r1)*S4,(cy_-r1)*S4,(cx_+r1)*S4,(cy_+r1)*S4],fill=255)
    # verdeckte Indizes unter Zeigern ergänzen: Raster aus vorhandenen Indizes, an verdeckten Stellen Index mit mittlerer Form zeichnen
    if spec.get('autohands') and 'hub' in spec:
        hx,hy=spec['hub'];ic=[]
        for c in comps(keep.copy()):
            cy_,cx_=c[:,0].mean(),c[:,1].mean();dd=math.hypot(cx_-hx,cy_-hy)
            if dd>spec.get('R',r)*.55: 
                dy_,dx_=c[:,0]-cy_,c[:,1]-cx_;cov=np.cov(np.vstack([dx_,dy_]));ev,evec=np.linalg.eigh(cov)
                ic.append(dict(n=len(c),d=dd,a=(math.degrees(math.atan2(cx_-hx,-(cy_-hy)))+360)%360,l=math.sqrt(12*ev[1]),wd=math.sqrt(12*max(ev[0],.2))))
        if len(ic)>=6:
            Rr=float(np.median([i['d'] for i in ic]));sm=[i for i in ic if abs(i['d']-Rr)<Rr*.08]
            nmed=np.median([i['n'] for i in sm]);typ=[i for i in sm if i['n']<nmed*1.6 and i['n']>nmed*.6] or sm
            Lm=float(np.median([i['l'] for i in typ]));Wm=float(np.median([i['wd'] for i in typ]))
            angs=[i['a'] for i in sm];off=float(np.median([((x+15)%30)-15 for x in angs]))
            handangs=[x[0] for x in (lg if spec.get('autohands') else [])]
            for k in range(12):
                A=(off+30*k)%360
                if any(abs(((A-x)+180)%360-180)<8 for x in angs): continue
                if not any(abs(((A-x)+180)%360-180)<9 for x in handangs): continue
                t=math.radians(A);cx_,cy_=hx+Rr*math.sin(t),hy-Rr*math.cos(t)
                if Lm/Wm<1.5:
                    rr=(Lm+Wm)/4;dr2.ellipse([(cx_-rr)*S4,(cy_-rr)*S4,(cx_+rr)*S4,(cy_+rr)*S4],fill=255)
                else:
                    ax_,ay_=math.sin(t),-math.cos(t);px_,py_=math.cos(t),math.sin(t);pts=[]
                    for u,v in((-Lm/2,-Wm/2),(Lm/2,-Wm/2),(Lm/2,Wm/2),(-Lm/2,Wm/2)): pts.append(((cx_+u*ax_+v*px_)*S4,(cy_+u*ay_+v*py_)*S4))
                    dr2.polygon(pts,fill=255)
                print('Index ergänzt bei',round(A),'°')
                for f in spec['shapes']:
                    if f['t']=='sword' and abs(((A-f['ang'])+180)%360-180)<9:
                        cut=Rr-max(Lm,Wm)*.62
                        f['w']=[x for x in f['w'] if x[0]<cut];
                        if f['w']: f['w'][-1]=[f['w'][-1][0],0]
                        # neu zeichnen ist nötig: Formen wurden schon gezeichnet -> Bereich jenseits cut löschen
                        t2=math.radians(f['ang']);ax2,ay2=math.sin(t2),-math.cos(t2);px2,py2=math.cos(t2),math.sin(t2)
                        quad=[(hx+cut*ax2+30*px2,hy+cut*ay2+30*py2),(hx+(cut+80)*ax2+30*px2,hy+(cut+80)*ay2+30*py2),(hx+(cut+80)*ax2-30*px2,hy+(cut+80)*ay2-30*py2),(hx+cut*ax2-30*px2,hy+cut*ay2-30*py2)]
                        dr.polygon([(x*S4,y*S4) for x,y in quad],fill=0)
    shp=np.array(shp.resize((w,h),Image.LANCZOS))>110
    und=np.array(shp2.resize((w,h),Image.LANCZOS))>110
    if lg:
        handm=np.zeros((h,w),bool);hx,hy=spec['hub'];yy2,xx2=np.mgrid[0:h,0:w];dx=xx2-hx;dy=yy2-hy
        for a_,role,mw,dm in lg:
            if role=='sec': mw=max(mw,3)
            t=math.radians(a_);ax_,ay_=math.sin(t),-math.cos(t);along=dx*ax_+dy*ay_;perp=np.abs(-dx*ay_+dy*ax_)
            handm|=(along>-4)&(along<dm+2)&(perp<mw/2+1.5)
    keep|=(shp if not spec.get('shapesafter') else False)|(und&~np.array(Image.fromarray((handm*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)))>0)
    for x0,y0,x1,y1 in spec.get('add',[]): # zusätzlich zu übernehmende Bereiche (alles Helle darin)
        sub=(L>=spec.get('thr',175)-40)&(S<=spec.get('sat',70)+10);keep[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]|=sub[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]
    # Indizes an bestimmten Winkeln neu setzen (z. B. wenn ein Zeiger darüber liegt): Kreis mit mittlerer Punktgröße auf dem Indexkreis
    if (spec.get('idxfix') or spec.get('autofill')) and 'hub' in spec:
        hx,hy=spec['hub'];cs=[c for c in comps(keep.copy()) if len(c)>30]
        info=[(math.hypot(c[:,1].mean()-hx,c[:,0].mean()-hy),c) for c in cs]
        ring=[(d,c) for d,c in info if d>spec.get('R',r)*.55]
        if ring:
            Rr=float(np.median([d for d,_ in ring]))
            if spec.get('autofill'):   # fehlende Stundenindizes finden: 12er-Raster, belegte Plätze, Rest ergänzen
                have=set()
                for d,c in ring:
                    if abs(d-Rr)<Rr*.14:
                        a_=(math.degrees(math.atan2(c[:,1].mean()-hx,-(c[:,0].mean()-hy)))+360)%360;k_=round(a_/30)%12
                        if abs(((a_-k_*30)+180)%360-180)<9: have.add(k_)
                miss=[k*30 for k in range(12) if k not in have and k*30 not in spec.get('noidx',[]) and k!=0]
                spec=dict(spec);spec['idxfix']=list(spec.get('idxfix',[]))+miss
                if miss: print('  ergänzt:',miss)
            isdot=lambda c:(c.max(0)-c.min(0)).max()<1.35*((c.max(0)-c.min(0)).min()+1)
            dots=[c for d,c in ring if abs(d-Rr)<Rr*.06 and isdot(c)]
            bars=[c for d,c in ring if abs(d-Rr)<Rr*.1 and not isdot(c)]
            yy5,xx5=np.mgrid[0:h,0:w]
            for A in spec['idxfix']:
                t=math.radians(A);px5,py5=hx+Rr*math.sin(t),hy-Rr*math.cos(t)
                if dots and len(dots)>=len(bars) and not spec.get('idxbar'):
                    rad=float(np.median([math.sqrt(len(c)/math.pi) for c in dots]))
                    keep[np.hypot(xx5-px5,yy5-py5)<rad*1.9]=False;keep[np.hypot(xx5-px5,yy5-py5)<=rad]=True
                    # Teil unter Stunden-/Minutenzeiger nicht leuchten lassen (Zeiger liegt darüber)
                    for a_,role,mw,dm in lg:
                        if role=='sec': continue
                        ta=math.radians(a_);ax6,ay6=math.sin(ta),-math.cos(ta);dx6=xx5-hx;dy6=yy5-hy;al6=dx6*ax6+dy6*ay6;pe6=np.abs(-dx6*ay6+dy6*ax6)
                        keep[(al6>0)&(al6<dm+3)&(pe6<mw/2+1.5)&(np.hypot(xx5-px5,yy5-py5)<=rad+1)]=False
                elif bars:   # Balken: Vorlage eines vorhandenen Balkens drehen
                    tb=bars[0];tcy,tcx=tb[:,0].mean(),tb[:,1].mean();ta=math.atan2(tcx-hx,-(tcy-hy));da=t-ta
                    keep[np.hypot(xx5-px5,yy5-py5)<math.sqrt(len(tb))*1.3]=False
                    ca,sa=math.cos(da),math.sin(da)
                    for yb,xb in tb:
                        vx,vy=xb-hx,yb-hy;nx=hx+vx*ca-vy*sa;ny=hy+vx*sa+vy*ca
                        for oy in (0,1):
                            for ox in (0,1):
                                X,Y=int(nx)+ox,int(ny)+oy
                                if 0<=X<w and 0<=Y<h: keep[Y,X]=True
    # Balkenindizes: Leuchtmasse nur als Mittelstreifen (Rand nach innen versetzt)
    if spec.get('idxinset'):
        ins=spec['idxinset'];hub0=spec.get('hub');new=np.zeros_like(keep);from PIL import ImageDraw as _ID
        im2=Image.new('L',(w*4,h*4),0);d2=_ID.Draw(im2)
        for c in comps(keep.copy()):
            cy_,cx_=c[:,0].mean(),c[:,1].mean()
            if hub0 and math.hypot(cx_-hub0[0],cy_-hub0[1])<spec.get('R',r)*.5:
                he=spec.get('handerode',0)
                if he:   # Zeiger aus dem Foto: nur die Innenfläche (Leuchtmasse) behalten, Zeigerkappe in der Mitte weglassen
                    y0h,x0h=c.min(0);sh=np.zeros((c[:,0].max()-y0h+3,c[:,1].max()-x0h+3),np.uint8);sh[c[:,0]-y0h+1,c[:,1]-x0h+1]=255
                    er=np.array(Image.fromarray(sh).filter(ImageFilter.MinFilter(2*he+1)))>127
                    ys3,xs3=np.nonzero(er);ys3=ys3+y0h-1;xs3=xs3+x0h-1
                    ok=np.hypot(xs3-hub0[0],ys3-hub0[1])>spec.get('capr',spec.get('R',r)*.09)
                    new[ys3[ok],xs3[ok]]=True
                else: new[c[:,0],c[:,1]]=True
                continue
            # dünne Anhängsel (Zeigerstriche über dem Index) abtrennen: Öffnen und größtes Stück behalten
            if len(c)>40:
                y0o,x0o=c.min(0);so=np.zeros((c[:,0].max()-y0o+5,c[:,1].max()-x0o+5),np.uint8);so[c[:,0]-y0o+2,c[:,1]-x0o+2]=255
                op=np.array(Image.fromarray(so).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5)))>127
                pcs=comps(op)
                if pcs:
                    big=max(pcs,key=len)
                    if len(big)>len(c)*.35: c=np.c_[big[:,0]+y0o-2,big[:,1]+x0o-2];cy_,cx_=c[:,0].mean(),c[:,1].mean()
            dy_,dx_=c[:,0]-cy_,c[:,1]-cx_
            if len(c)<6: continue
            ev,evec=np.linalg.eigh(np.cov(np.vstack([dx_,dy_])));v=evec[:,1];u=np.array([-v[1],v[0]])
            pa=dx_*v[0]+dy_*v[1];pb=dx_*u[0]+dy_*u[1]
            L_=pa.max()-pa.min();W_=pb.max()-pb.min()
            ell=len(c)/max(1,math.pi/4*(L_+1)*(W_+1))
            # Rundheit über den Rand: Abstand der Randpixel zum Mittelpunkt muss nahezu konstant sein (Ziffern 6/9 fallen heraus)
            S_=set(map(tuple,c.tolist()));edge=np.array([p for p in c.tolist() if (p[0]+1,p[1]) not in S_ or (p[0]-1,p[1]) not in S_ or (p[0],p[1]+1) not in S_ or (p[0],p[1]-1) not in S_])
            rd=np.hypot(edge[:,1]-cx_,edge[:,0]-cy_) if len(edge) else np.array([0.,1.])
            circ=rd.std()/max(rd.mean(),1e-6)
            if spec.get('dotr',1)==0 and L_<W_*1.3 and .8<ell<1.2: continue   # Kreise werden per Form gesetzt
            if L_<W_*1.3 and .8<ell<1.2 and circ<.09:   # runde Indizes: Leuchtmasse als exakter Kreis in der Mitte der Einfassung
                rr=math.sqrt(len(c)/math.pi)*spec.get('dotr',.68)
                d2.ellipse([(cx_-rr)*4,(cy_-rr)*4,(cx_+rr)*4,(cy_+rr)*4],fill=255);continue
            if L_<W_*1.6 or len(c)/max(1,L_*W_)<.72:   # Punkte, Dreiecke, Ziffern: Leuchtmasse nur innerhalb der Einfassung (nach innen schrumpfen)
                fillr=len(c)/max(1,(c[:,0].max()-c[:,0].min()+1)*(c[:,1].max()-c[:,1].min()+1))
                e=max(1,int(round(min(L_,W_)*spec.get('dotshrink',.17))))
                y0,x0=c.min(0);sub=np.zeros((c[:,0].max()-y0+3,c[:,1].max()-x0+3),np.uint8);sub[c[:,0]-y0+1,c[:,1]-x0+1]=255
                while True:   # nicht zu stark schrumpfen: mindestens ~40 % der Fläche behalten (Ziffern mit dünnen Strichen)
                    er=np.array(Image.fromarray(sub).filter(ImageFilter.MinFilter(2*e+1)))>127
                    if er.sum()>=len(c)*.4 or e<=1: break
                    e-=1
                ys2,xs2=np.nonzero(er);new[ys2+y0-1,xs2+x0-1]=True;continue
            ca=(pa.max()+pa.min())/2;cb=(pb.max()+pb.min())/2;l2=L_*(1-ins)/2;w2=W_*(1-2*ins)/2
            pts=[(cx_+(ca+sa*l2)*v[0]+(cb+sb*w2)*u[0],cy_+(ca+sa*l2)*v[1]+(cb+sb*w2)*u[1]) for sa,sb in((-1,-1),(1,-1),(1,1),(-1,1))]
            d2.polygon([(x*4,y*4) for x,y in pts],fill=255)
        keep=new|(np.array(im2.resize((w,h),Image.LANCZOS))>110)
    if spec.get('shapesafter'): keep|=shp   # gezeichnete Zeigerformen unverändert übernehmen (nicht schrumpfen/abtrennen)
    # Kanten glätten
    mk=Image.fromarray((keep*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.7))
    col=(185,232,255) if spec.get('col','g')=='b' else (175,255,205)
    ov=Image.new('RGBA',(w,h),col+(0,));ov.putalpha(mk)
    # auf max. 900 px Höhe verkleinern
    if h>900: ov=ov.resize((round(w*900/h),900),Image.LANCZOS)
    # Kanten bei allen Masken gleich fest: weiche Kante straffen, damit Leuchtkraft/Glow nicht von der Bildgröße abhängt
    al=np.asarray(ov.getchannel('A')).astype(np.float32);ov.putalpha(Image.fromarray(np.clip((al-40)*255/150,0,255).astype(np.uint8)))
    return ov,keep
if __name__=='__main__':
    specs=json.load(open(sys.argv[1]))
    for img,spec in specs.items():
        ov,keep=gen(img,spec)
        name=img.split('/')[-1].rsplit('.',1)[0]+'.png'
        ov.save((OUT if 'OUT' in globals() else ROOT+'assets/watches/lume/')+name,optimize=True)
        # Vorschau
        base=Image.open(ROOT+img).convert('RGB');pv=base.point(lambda v:int(v*.35)).convert('RGBA')
        pv.alpha_composite(ov.resize(base.size));pv.convert('RGB').save('/tmp/pv_'+name)
        print(name,int(keep.sum()))
