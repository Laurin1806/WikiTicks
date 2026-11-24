"""Vermessene Leuchtmaske. Parameter je Bild (Pixel im Originalbild):
hub [x,y], R (Bezugsradius), ri/ro (Index innen/außen als Anteil von R), w (Breite px),
skip [Stunden], short {Stunde: [ri,ro]}, dbl12 (Abstand der Doppelbalken bei 12, px),
hands [[Winkel, r0, r1, Breite]] (r als Anteil von R), strips [[x0,y0,x1,y1,w]], dots [[x,y,r]],
vint (cremefarben), minutes {r0,r1,w} (Minutenpunkte/-striche am Rand)."""
import json,sys,math,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFilter
import os;ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/';D=os.path.dirname(os.path.abspath(__file__))+'/'
def build(n,p,out):
    im=Image.open(ROOT+'assets/watches/'+n+'.jpg').convert('RGB');W,H=im.size
    hx,hy=p['hub'];R=p['R'];S=[];w=p.get('w',R*.03)
    pt=lambda a,r:(hx+math.sin(math.radians(a))*r,hy-math.cos(math.radians(a))*r)
    for h in range(12):
        if h in p.get('skip',[]): continue
        ri,ro=p.get('short',{}).get(str(h),[p.get('ri',.75),p.get('ro',.9)])
        if h==0 and p.get('dbl12'):
            for o in (-1,1): S.append(((hx+o*p['dbl12'],hy-ro*R),(hx+o*p['dbl12'],hy-ri*R),w))
            continue
        S.append((pt(h*30,ri*R),pt(h*30,ro*R),w))
    for a,r0,r1,hw in p.get('hands',[]): S.append((pt(a,r0*R),pt(a,r1*R),hw))
    for x0,y0,x1,y1,sw in p.get('strips',[]): S.append(((x0,y0),(x1,y1),sw))
    m=Image.new('L',(W*4,H*4),0);d=ImageDraw.Draw(m)
    for (a,b),(c,e),sw in [((s[0][0],s[0][1]),(s[1][0],s[1][1]),s[2]) for s in S]:
        d.line([(a*4,b*4),(c*4,e*4)],fill=255,width=max(4,int(sw*4)))
        for x,y in ((a,b),(c,e)): d.ellipse([(x-sw/2)*4,(y-sw/2)*4,(x+sw/2)*4,(y+sw/2)*4],fill=255)
    for x,y,r in p.get('dots',[]): d.ellipse([(x-r)*4,(y-r)*4,(x+r)*4,(y+r)*4],fill=255)
    if p.get('minutes'):
        q=p['minutes']
        for k in range(60):
            if k%5==0 and not q.get('all'): continue
            (a,b),(c,e)=pt(k*6,q['r0']*R),pt(k*6,q['r1']*R);d.line([(a*4,b*4),(c*4,e*4)],fill=255,width=max(4,int(q['w']*4)))
    if p.get('sel'):   # farbige Leuchtmasse per Farbauswahl (z. B. beige Ziffern), nur innerhalb von rsel um die Mitte
        q=p['sel'];A=np.asarray(im).astype(int);Lm=A.mean(2);yy,xx=np.mgrid[0:H,0:W]
        mk=(A[:,:,0]-A[:,:,2]>=q.get('warm',22))&(Lm>=q.get('lmin',110))&(np.hypot(xx-hx,yy-hy)<=q['r']*R)
        if q.get('cool'): mk=(np.abs(A[:,:,0]-A[:,:,2])<=q['cool'])&(Lm>=q.get('lmin',150))&(np.hypot(xx-hx,yy-hy)<=q['r']*R)
        for x0,y0,x1,y1 in q.get('ex',[]): mk[int(y0):int(y1),int(x0):int(x1)]=False
        e=q.get('erode',0)
        mi=Image.fromarray((mk*255).astype(np.uint8))
        if e: mi=mi.filter(ImageFilter.MinFilter(2*e+1))
        sm=np.asarray(mi.resize((W*4,H*4),Image.NEAREST))>127
        m=Image.fromarray(np.maximum(np.asarray(m),sm*255).astype(np.uint8))
    m=m.resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(.5))
    al=np.clip((np.asarray(m).astype(float)-30)*255/170,0,255).astype(np.uint8)
    col=(255,236,190) if p.get('vint') else (175,255,205)
    ov=Image.new('RGBA',(W,H),col+(0,));ov.putalpha(Image.fromarray(al))
    if H>900: ov=ov.resize((round(W*900/H),900),Image.LANCZOS)
    ov.save(out+n+'.png',optimize=True)
if __name__=='__main__':
    P=json.load(open(D+'lume-meas.json'))
    for n in (sys.argv[1:] or P):
        p=P[n];build(n,p,ROOT+'assets/watches/lume/')
        print(n)
