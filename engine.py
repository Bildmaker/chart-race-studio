# -*- coding: utf-8 -*-
"""ChartRace Studio - Render-Engine.
Erzeugt animierte Bar-Chart-Race-Videos (9:16) fuer Social Media.
Daten: live ueber yfinance (falls installiert) mit Offline-Fallback (data.py).
"""
import os, sys, math, shutil, tempfile, subprocess, datetime, wave
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data as D

# ---------------------------------------------------------------- presets
# offline_key: 'gold' | 'btc' | 'nvda' | None
PRESETS = {
    "Gold":      {"ticker": "GC=F",   "color": "#FFC93C", "offline": "gold"},
    "Bitcoin":   {"ticker": "BTC-USD","color": "#F7931A", "offline": "btc"},
    "Nvidia":    {"ticker": "NVDA",   "color": "#76D900", "offline": "nvda"},
    "Ethereum":  {"ticker": "ETH-USD","color": "#8A92B2", "offline": None},
    "Apple":     {"ticker": "AAPL",   "color": "#5AC8FA", "offline": None},
    "Microsoft": {"ticker": "MSFT",   "color": "#00A4EF", "offline": None},
    "Tesla":     {"ticker": "TSLA",   "color": "#E82127", "offline": None},
    "Amazon":    {"ticker": "AMZN",   "color": "#FF9900", "offline": None},
    "Meta":      {"ticker": "META",   "color": "#0668E1", "offline": None},
    "Google":    {"ticker": "GOOGL",  "color": "#EA4335", "offline": None},
    "S&P 500":   {"ticker": "^GSPC",  "color": "#34C759", "offline": None},
    "Silber":    {"ticker": "SI=F",   "color": "#C0C0C0", "offline": None},
}
PALETTE = ["#FFC93C","#F7931A","#76D900","#5AC8FA","#E82127","#8A92B2",
           "#00A4EF","#EA4335","#34C759","#C0C0C0"]

def glow_of(hexc):
    h = hexc.lstrip("#"); r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    f = lambda c: int(c+(255-c)*0.45)
    return "#%02X%02X%02X" % (f(r),f(g),f(b))

THEMES = {
    "dark":  {"bg":["#080812","#11111f","#0a0a16"], "fig":"#080812",
              "text":"#ffffff","sub":"#7d7d99","year":"#ffffff","month":"#6a6a8c",
              "track":"#16161f","track_a":0.6,"vlight":"#ffffff","tlbg":"#2a2a3a",
              "tlfg":"#9a9aff","tllabel":"#55556e","val_out":"#ffffff","val_in":"#0a0a16"},
    "light": {"bg":["#f3f3fa","#e9e9f4","#f3f3fa"], "fig":"#f3f3fa",
              "text":"#14141c","sub":"#6a6a82","year":"#14141c","month":"#9a9ab2",
              "track":"#dadae6","track_a":0.9,"vlight":"#ffffff","tlbg":"#cfcfe0",
              "tlfg":"#5b5be0","tllabel":"#9a9ab2","val_out":"#14141c","val_in":"#0a0a16"},
}

MONTHS_DE = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
W,H,DPI,FPS = 1080,1920,100,30

def midx(year, month):  # month index, 0 = 2012-01
    return (year-2012)*12 + (month-1)

def date_label(t):
    yr = 2012 + int(t)//12
    mo = int(t)%12
    return MONTHS_DE[mo], yr

def fmt_eur(v, cur="€"):
    if v < 1000:   return f"{v:,.0f} {cur}".replace(",",".")
    if v < 1e6:    return f"{v:,.0f} {cur}".replace(",","X").replace(".",",").replace("X",".")
    if v < 1e9:    return f"{v/1e6:,.1f} Mio {cur}".replace(".",",")
    return f"{v/1e9:,.2f} Mrd {cur}".replace(".",",")

def fmt_mult(m):
    return (f"{m:,.1f}×".replace(".",",") if m < 100 else f"{m:,.0f}×".replace(",","."))

# ---------------------------------------------------------------- data
def _offline_series(key):
    if key == "gold":
        mi = np.append(np.arange(len(D.GOLD)), 173); v = np.array(D.GOLD+[D.GOLD_FINAL])
    elif key == "btc":
        mi = np.append(np.arange(len(D.BTC)), 173);  v = np.array(D.BTC+[D.BTC_FINAL])
    elif key == "nvda":
        mi = np.array([a for a,_ in D.NVDA_ANCHORS], float)
        v  = np.array([b for _,b in D.NVDA_ANCHORS], float)
    else:
        raise KeyError(key)
    return mi, v

def load_series(name, ticker, offline_key, start_mi, end_mi, prefer_live=True, log=print):
    """Return (mi_array, price_array, source). Live (yfinance) mit Offline-Fallback."""
    live_reason=None
    if prefer_live:
        yf=None
        try:
            import yfinance as yf
        except Exception:
            live_reason="yfinance nicht installiert - bitte install.bat ausfuehren"
            log("    ! "+live_reason)
        if yf is not None:
            sy=2012+start_mi//12; sm=start_mi%12+1; start=f"{sy:04d}-{sm:02d}-01"
            df=None
            try:
                log(f"  - {name}: Live ({ticker}) ab {start} ...")
                d=yf.download(ticker,start=start,interval="1mo",auto_adjust=True,progress=False)
                if d is not None and len(d)>2: df=d
            except Exception as e:
                live_reason=f"download-Fehler: {e}"
            if df is None:  # zweiter, robusterer Weg
                try:
                    d=yf.Ticker(ticker).history(period="max",interval="1mo",auto_adjust=True)
                    if d is not None and len(d)>2: df=d
                except Exception as e:
                    live_reason=live_reason or f"history-Fehler: {e}"
            if df is not None:
                close=df["Close"]
                if hasattr(close,"columns"): close=close.iloc[:,0]
                close=close.dropna()
                mi=np.array([midx(d.year,d.month) for d in close.index],float)
                v=np.asarray(close.values,dtype=float)
                if len(mi)>2:
                    log(f"    OK {len(mi)} Monatswerte live geladen")
                    return mi, v, "live"
                live_reason=live_reason or "keine verwertbaren Kurse erhalten"
            else:
                live_reason=live_reason or f"keine Daten von Yahoo fuer '{ticker}'"
            log("    ! Live fehlgeschlagen: "+str(live_reason))
    if offline_key:
        mi, v = _offline_series(offline_key)
        return mi, v, "offline"
    extra=f" (Live-Grund: {live_reason})" if live_reason else ""
    raise RuntimeError(
        f"Fuer '{name}' sind keine Offline-Daten vorhanden{extra}. "
        f"Bitte Internet + yfinance sicherstellen (einmal install.bat ausfuehren) "
        f"oder ein Asset mit Offline-Daten waehlen: Gold, Bitcoin, Nvidia.")

# ---------------------------------------------------------------- music
def make_music(path, dur):
    SR=44100; N=int(SR*dur); out=np.zeros(N); BPM=125.0; beat=60.0/BPM
    def tone(freq,start,length,kind="saw",a=0.005,d=0.12,amp=0.3):
        i0=int(start*SR); i1=min(N,int((start+length)*SR))
        if i0>=N or i1<=i0: return
        n=i1-i0; tt=np.arange(n)/SR; ph=2*np.pi*freq*tt
        if kind=="saw": w=2*(ph/(2*np.pi)%1)-1
        elif kind=="square": w=np.sign(np.sin(ph))
        else: w=np.sin(ph)
        eg=np.ones(n); ai=max(1,min(int(a*SR),n)); eg[:ai]=np.linspace(0,1,ai); eg*=np.exp(-tt/d)
        out[i0:i1]+=amp*w*eg
    def kick(start,amp=0.95):
        i0=int(start*SR); i1=min(N,int((start+0.18)*SR))
        if i0>=N or i1<=i0: return
        n=i1-i0; tt=np.arange(n)/SR; f=110*np.exp(-tt/0.03)+45
        ph=2*np.pi*np.cumsum(f)/SR; out[i0:i1]+=amp*np.sin(ph)*np.exp(-tt/0.10)
    def hat(start,amp=0.18):
        i0=int(start*SR); i1=min(N,int((start+0.04)*SR))
        if i0>=N or i1<=i0: return
        n=i1-i0; tt=np.arange(n)/SR; out[i0:i1]+=amp*np.random.randn(n)*np.exp(-tt/0.012)
    nf=lambda s:440.0*2**(s/12.0)
    prog=[-12,-16,-9,-2]; chord={-12:[0,3,7],-16:[0,4,7],-9:[0,4,7],-2:[0,4,7]}
    nb=int(dur/beat)+1
    for b in range(nb):
        kick(b*beat); hat(b*beat+beat*0.5)
        if b%2==1: hat(b*beat+beat*0.25,0.10)
    chunk=2*beat; nc=int(dur/chunk)+1
    for c in range(nc):
        root=prog[c%4]; rootf=nf(root-12)
        for k in range(4): tone(rootf,c*chunk+k*(chunk/4),chunk/4*0.9,"square",d=0.18,amp=0.22)
        arp=[root+s for s in chord[root]]+[root+12]
        for k in range(8): tone(nf(arp[k%len(arp)]),c*chunk+k*(chunk/8),chunk/8*0.95,"saw",d=0.10,amp=0.13)
        for s in chord[root]: tone(nf(root+s),c*chunk,chunk*0.98,"sine",a=0.05,d=1.2,amp=0.06)
    rs=max(0,dur-2.2); i0=int(rs*SR); tt=np.arange(N-i0)/SR
    if len(tt)>0:
        fr=200*2**(tt/1.1); ph=2*np.pi*np.cumsum(fr)/SR; out[i0:]+=0.18*np.sin(ph)*(tt/2.2)
    out=out/max(1e-9,np.max(np.abs(out)))*0.92; out=np.tanh(out*1.2)/np.tanh(1.2)
    fo=int(0.15*SR); out[-fo:]*=np.linspace(1,0,fo)
    pcm=(out*32767).astype(np.int16); st=np.repeat(pcm.reshape(-1,1),2,1).reshape(-1)
    w=wave.open(path,"wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(st.tobytes()); w.close()

# ---------------------------------------------------------------- rendering
def _bg(ax, th):
    grad=np.linspace(0,1,256).reshape(-1,1)
    cmap=LinearSegmentedColormap.from_list("bg",th["bg"])
    ax.imshow(grad,extent=[0,W,0,H],aspect="auto",cmap=cmap,origin="lower",zorder=0)

def _logfrac(v,vmin,vmax):
    if vmax<=vmin*1.0001 or vmin<=0: return 1.0
    f=(math.log(v)-math.log(vmin))/(math.log(vmax)-math.log(vmin))
    return 0.16+0.84*max(0.0,min(1.0,f))

def _layout(n):
    if n<=3: return 180,78
    if n==4: return 150,62
    if n==5: return 126,52
    return 102,42

def _frame(path, assets, vals, ydisp, t, th, invest, cur, start_year,
           winner=None, blink=None):
    n=len(assets); barh,gap=_layout(n)
    BARX0=330; BARW=W-BARX0-90; NAMEX=300
    total=n*barh+(n-1)*gap; center=H*0.45
    block_top=center+total/2-barh
    vmax=max(vals.values()); vmin=min(vals.values())
    fig=plt.figure(figsize=(W/DPI,H/DPI),dpi=DPI)
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off"); _bg(ax,th)
    ax.text(W/2,H-130,"AUS %s WURDEN…"%fmt_eur(invest,cur),ha="center",va="center",
            color=th["text"],fontsize=44,fontweight="bold")
    names=" · ".join(a["name"] for a in assets)
    ax.text(W/2,H-188,"%s   |   seit %d"%(names,start_year),ha="center",va="center",
            color=th["sub"],fontsize=23,fontweight="bold")
    mo,yr=date_label(t)
    ax.text(W/2,H-340,f"{yr}",ha="center",va="center",color=th["year"],fontsize=140,fontweight="bold")
    ax.text(W/2,H-430,f"{mo}",ha="center",va="center",color=th["month"],fontsize=34,fontweight="bold")
    for a in assets:
        nm=a["name"]; c=a["color"]; gc=glow_of(c); v=vals[nm]
        y=block_top - ydisp[nm]*(barh+gap)
        frac=_logfrac(v,vmin,vmax); bw=max(BARW*frac,70)
        ax.add_patch(FancyBboxPatch((BARX0,y),BARW,barh,boxstyle="round,pad=0,rounding_size=38",
            lw=0,facecolor=th["track"],alpha=th["track_a"],zorder=1))
        gb=(blink if (blink is not None and nm==winner) else 0.0)
        for dx,al in [(24,0.06),(14,0.09),(7,0.13)]:
            ax.add_patch(FancyBboxPatch((BARX0-dx,y-dx),bw+2*dx,barh+2*dx,
                boxstyle="round,pad=0,rounding_size=40",lw=0,facecolor=gc,
                alpha=min(1.0,al+gb*0.9),zorder=2))
        ax.add_patch(FancyBboxPatch((BARX0,y),bw,barh,boxstyle="round,pad=0,rounding_size=36",
            lw=0,facecolor=c,zorder=3))
        ax.add_patch(FancyBboxPatch((BARX0,y+barh*0.55),bw,barh*0.45,
            boxstyle="round,pad=0,rounding_size=36",lw=0,facecolor=th["vlight"],alpha=0.10,zorder=4))
        if blink is not None and nm==winner:
            ax.add_patch(FancyBboxPatch((BARX0-6,y-6),bw+12,barh+12,boxstyle="round,pad=0,rounding_size=38",
                lw=6,edgecolor=th["text"],facecolor="none",alpha=blink,zorder=7))
            ax.text(BARX0+bw/2,y+barh+40,"★ BESTE PERFORMANCE ★",ha="center",va="center",
                color=th["text"],fontsize=28,fontweight="bold",alpha=0.55+0.45*blink,zorder=8)
        fs_name=33 if n<=4 else 27
        ax.text(NAMEX,y+barh/2,nm.upper(),ha="right",va="center",color=c,
                fontsize=fs_name,fontweight="bold",zorder=6)
        vtxt=fmt_eur(v,cur); mtxt=fmt_mult(v/invest); end=BARX0+bw
        fs_v=42 if n<=4 else 34
        if end>W-340:
            ax.text(end-34,y+barh*0.60,vtxt,ha="right",va="center",color=th["val_in"],fontsize=fs_v,fontweight="bold",zorder=6)
            ax.text(end-34,y+barh*0.25,mtxt,ha="right",va="center",color=th["val_in"],fontsize=fs_v*0.64,fontweight="bold",alpha=0.72,zorder=6)
        else:
            ax.text(end+26,y+barh*0.60,vtxt,ha="left",va="center",color=th["val_out"],fontsize=fs_v,fontweight="bold",zorder=6)
            ax.text(end+26,y+barh*0.25,mtxt,ha="left",va="center",color=c,fontsize=fs_v*0.64,fontweight="bold",zorder=6)
    # timeline
    sy=start_year; mi0=int(t); 
    return fig, ax

def render_video(cfg, progress=None, log=print):
    """cfg keys: assets(list of names), invest, start_year, start_month,
       duration, hold, blink(bool), look('dark'/'light'), music(bool),
       out_path, currency, prefer_live(bool)."""
    def report(p,msg):
        if progress: progress(p,msg)
        log(msg)
    assets_in = cfg["assets"]; invest=float(cfg["invest"])
    sy=int(cfg["start_year"]); sm=int(cfg.get("start_month",1))
    dur=float(cfg["duration"]); hold=float(cfg.get("hold",2.0))
    blink=bool(cfg.get("blink",True)); look=cfg.get("look","dark")
    music=bool(cfg.get("music",True)); cur=cfg.get("currency","€")
    prefer_live=bool(cfg.get("prefer_live",True))
    th=THEMES.get(look,THEMES["dark"])
    today=datetime.date.today()
    start_mi=midx(sy,sm); end_mi=midx(today.year,today.month)
    if end_mi<=start_mi: end_mi=start_mi+12

    # build assets with data
    report(2,"Lade Kursdaten …")
    assets=[]
    for i,nm in enumerate(assets_in):
        pre=PRESETS.get(nm, {"ticker":nm,"color":PALETTE[i%len(PALETTE)],"offline":None})
        mi,v,src=load_series(nm,pre["ticker"],pre.get("offline"),start_mi,end_mi,prefer_live,log)
        assets.append({"name":nm,"color":pre["color"],"mi":mi,"v":v,"src":src})
    def price(a,t): return float(np.interp(t,a["mi"],a["v"]))
    for a in assets:
        a["p0"]=price(a,start_mi)
        if a["p0"]<=0: a["p0"]=price(a,a["mi"][0])
    def values_at(t):
        return {a["name"]: invest*price(a,t)/a["p0"] for a in assets}

    endvals=values_at(end_mi)
    winner=max(endvals,key=lambda k:endvals[k])
    report(8,f"Sieger steht fest: {winner} ({fmt_eur(endvals[winner],cur)})")

    total=int(round(dur*FPS)); holdf=int(round(hold*FPS)); racef=max(2,total-holdf)
    tmp=tempfile.mkdtemp(prefix="crs_")
    ydisp={a["name"]:None for a in assets}; yd={}
    NAMES=[a["name"] for a in assets]
    def step_order(t):
        nonlocal yd
        vals=values_at(t); order=sorted(NAMES,key=lambda k:vals[k],reverse=True)
        tg={n:order.index(n) for n in NAMES}
        if not yd: yd={n:float(tg[n]) for n in NAMES}
        else:
            for n in NAMES: yd[n]+=(tg[n]-yd[n])*0.22
        return vals
    try:
        for i in range(total):
            if i<racef:
                t=start_mi+(i/(racef-1))*(end_mi-start_mi); bl=None
            else:
                t=end_mi; ph=(i-racef)/FPS; bl=0.5+0.5*math.sin(ph*2*math.pi*2.5)
            vals=step_order(t)
            fig,ax=_frame(None,assets,vals,yd,t,th,invest,cur,sy,
                          winner=winner,blink=(bl if blink else None))
            # timeline
            tlx0,tlx1,tly=80,W-80,150
            ax.plot([tlx0,tlx1],[tly,tly],color=th["tlbg"],lw=6,solid_capstyle="round",zorder=2)
            fr=(t-start_mi)/max(1,(end_mi-start_mi)); px=tlx0+(tlx1-tlx0)*fr
            ax.plot([tlx0,px],[tly,tly],color=th["tlfg"],lw=6,solid_capstyle="round",zorder=3)
            ax.scatter([px],[tly],s=180,color=th["text"],zorder=4,edgecolors=th["tlfg"],linewidths=2)
            ax.text(tlx0,tly-44,f"{sy}",ha="left",va="center",color=th["tllabel"],fontsize=22,fontweight="bold")
            ax.text(tlx1,tly-44,f"{today.year}",ha="right",va="center",color=th["tllabel"],fontsize=22,fontweight="bold")
            fig.savefig(os.path.join(tmp,f"f{i:05d}.png"),facecolor=th["fig"]); plt.close(fig)
            if i%10==0:
                report(10+int(78*i/total),f"Rendere Frame {i+1}/{total} …")
        # music
        audio=None
        if music:
            report(90,"Erzeuge Musik …"); audio=os.path.join(tmp,"music.wav"); make_music(audio,dur)
        report(92,"Setze Video zusammen (ffmpeg) …")
        ff=_ffmpeg_exe()
        out=cfg["out_path"]
        cmd=[ff,"-y","-framerate",str(FPS),"-i",os.path.join(tmp,"f%05d.png")]
        if audio: cmd+=["-i",audio]
        cmd+=["-c:v","libx264","-pix_fmt","yuv420p","-crf","19","-preset","medium"]
        if audio: cmd+=["-c:a","aac","-b:a","192k","-shortest"]
        cmd+=["-movflags","+faststart",out]
        subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        report(100,f"Fertig: {out}")
        return out
    finally:
        shutil.rmtree(tmp,ignore_errors=True)

def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe=shutil.which("ffmpeg")
        if exe: return exe
        raise RuntimeError("ffmpeg nicht gefunden. Bitte 'pip install imageio-ffmpeg' "
                           "ausführen oder ffmpeg installieren.")
