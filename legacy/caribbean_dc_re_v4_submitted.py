#!/usr/bin/env python3
"""
PyPSA DC-RE Co-planning: Caribbean SIDS (Production v4)
Cases: Trinidad (single-bus, Brechin Castle 92MW), Jamaica (4-bus JPS)
2190h (Q1), BTM BESS, workload flex 70/30, post-hoc DRO + siting.
Figures: fig1a (Jamaica geo), fig1b (Trinidad geo), fig2 (results bars)
"""
import numpy as np, pandas as pd, pypsa, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import warnings, time, os, json
warnings.filterwarnings('ignore')

H = 2190
SNAP = pd.date_range('2024-01-01', periods=H, freq='h')
FRAC = H / 8760
FDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
os.makedirs(FDIR, exist_ok=True)

EF = {'diesel':.65,'hfo':.72,'gas':.37,'lng':.37,'solar':0,'wind':0,
      'geothermal':0,'hydro':0,'load_shed':0}

def crf(r,n): return r*(1+r)**n/((1+r)**n-1) if r>0 else 1/n
def acap(capex,opex,life,r): return (crf(r,life)*capex+opex)*1000*FRAC

# ── Profiles ──
def ar1(n,rho=.85,sig=1.,seed=42):
    rng=np.random.RandomState(seed); e=rng.normal(0,sig*np.sqrt(1-rho**2),n)
    x=np.zeros(n); x[0]=e[0]
    for i in range(1,n): x[i]=rho*x[i-1]+e[i]
    return x
def solar_p(cf,lat,seed=42):
    t=np.arange(H); hod=t%24; doy=t//24
    decl=23.45*np.sin(2*np.pi*(doy-81)/365); ha=15*(hod-12)
    cz=np.maximum(0,np.sin(np.radians(lat))*np.sin(np.radians(decl))+
       np.cos(np.radians(lat))*np.cos(np.radians(decl))*np.cos(np.radians(ha)))
    p=cz*(0.72+0.12*np.cos(2*np.pi*(doy-75)/365))*np.clip(1+ar1(H,.85,.15,seed),.3,1)
    if p.mean()>0: p*=cf/p.mean()
    return np.clip(p,0,1)
def wind_p(cf,seed=99):
    ws=np.maximum(0,(ar1(H,.92,2.5,seed)+8.5)*(1+.2*np.cos(2*np.pi*(np.arange(H)//24-45)/365)))
    o=np.zeros(H); m=(ws>=3.5)&(ws<12)
    o[m]=((ws[m]-3.5)/8.5)**3; o[(ws>=12)&(ws<=25)]=1.
    if o.mean()>0: o*=cf/o.mean()
    return np.clip(o,0,1)
def load_p(peak,seed=55):
    t=np.arange(H); hod=t%24; doy=t//24; dow=(t//24)%7
    d=.60+.15*np.exp(-.5*((hod-11)/2.5)**2)+.20*np.exp(-.5*((hod-20)/2)**2)
    Ta=28.5+3.5*np.sin(2*np.pi*(hod-15)/24)+1.5*np.sin(2*np.pi*(doy-200)/365)+ar1(H,.95,.8,seed)
    ld=peak*d*np.where(dow>=5,.88,1.)*(1+.012*np.maximum(0,Ta-27))*(1+ar1(H,.90,.03,seed+1))
    return np.clip(ld,peak*.30,peak*1.15), Ta
def dc_load(it_mw,pue,flex,Ta):
    hod=np.arange(H)%24; dow=(np.arange(H)//24)%7
    it=it_mw*(1+.06*np.cos(2*np.pi*(hod-14)/24))*np.where(dow>=5,.88,1.)
    total=it*pue*(1+.005*(Ta[:H]-25))
    inf=total*(1-flex)
    flx=pd.Series(total*flex,index=SNAP).resample('D').mean().reindex(SNAP).ffill().bfill().values
    return total,inf,flx

# ── Components ──
def add_bess(n,bus,pfx,emax,r,btm=False):
    ce=acap(250 if btm else 210,5 if btm else 4,12 if btm else 15,r)/1000
    cp=acap(280 if btm else 230,6 if btm else 5,12 if btm else 15,r)/1000
    eff=.92 if btm else .93; tag='btm' if btm else 'bes'
    bb=f"{pfx}_{tag}b"; n.add("Bus",bb,carrier="battery")
    n.add("Store",f"{pfx}_{tag}s",bus=bb,e_nom_extendable=True,e_nom_max=emax,
          capital_cost=ce,e_cyclic=True)
    n.add("Link",f"{pfx}_{tag}c",bus0=bus,bus1=bb,p_nom_extendable=True,
          p_nom_max=emax/4,efficiency=eff,capital_cost=cp*.5)
    n.add("Link",f"{pfx}_{tag}d",bus0=bb,bus1=bus,p_nom_extendable=True,
          p_nom_max=emax/4,efficiency=eff,capital_cost=cp*.5)
def add_h2(n,bus,pfx,mx,r):
    hb=f"{pfx}_h2"; n.add("Bus",hb,carrier="hydrogen")
    n.add("Link",f"{pfx}_elz",bus0=bus,bus1=hb,p_nom_extendable=True,p_nom_max=mx,
          efficiency=.65,capital_cost=acap(1400,28,20,r))
    n.add("Store",f"{pfx}_h2s",bus=hb,e_nom_extendable=True,e_nom_max=200,
          capital_cost=acap(15,.3,25,r)/1000,e_cyclic=True)
    n.add("Link",f"{pfx}_fc",bus0=hb,bus1=bus,p_nom_extendable=True,p_nom_max=mx//2,
          efficiency=.55,capital_cost=acap(1500,30,15,r))

# ═══════════════════════════════════════════════════════
# CASE A: Trinidad — Brechin Castle 92MW, gas fleet, 5MW DC
# ═══════════════════════════════════════════════════════
def case_a():
    r=.07; n=pypsa.Network(); n.set_snapshots(SNAP)
    n.add("Bus","TT",carrier="AC",x=-61.3,y=10.5)
    # NGC gas fleet ~1800MW
    n.add("Generator","TT_gas",bus="TT",carrier="gas",p_nom=1800,marginal_cost=55,p_min_pu=.25)
    # Brechin Castle Solar: 92 MWac (bp/Shell/NGC JV, near Point Lisas, commissioned Q4 2025)
    n.add("Generator","TT_brechin",bus="TT",carrier="solar",p_nom=92,marginal_cost=0,
          p_max_pu=solar_p(.18,10.3,10))
    # Extendable
    n.add("Generator","TT_sol1",bus="TT",carrier="solar",p_nom_extendable=True,p_nom_max=300,
          capital_cost=acap(1100,12,25,r),marginal_cost=.5,p_max_pu=solar_p(.18,10.5,11))
    n.add("Generator","TT_wnd1",bus="TT",carrier="wind",p_nom_extendable=True,p_nom_max=100,
          capital_cost=acap(1600,35,20,r),marginal_cost=1.,p_max_pu=wind_p(.22,12))
    add_bess(n,"TT","TT",400,r); add_h2(n,"TT","TT",20,r)
    n.add("Generator","TT_voll",bus="TT",carrier="load_shed",p_nom=1e4,marginal_cost=2000)
    ld,Ta=load_p(1300,20); n.add("Load","TT_ld",bus="TT",p_set=ld*1.07)
    _,inf,flx=dc_load(5,1.5,.30,Ta)
    n.add("Load","TT_dci",bus="TT",p_set=inf)
    n.add("Load","TT_dcf",bus="TT",p_set=flx)
    add_bess(n,"TT","TTb",5*1.5*4,r,btm=True)
    return n

# ═══════════════════════════════════════════════════════
# CASE B: Jamaica — 4-bus JPS topology, 15MW DC at Kingston
# ═══════════════════════════════════════════════════════
def case_b():
    r=.10; n=pypsa.Network(); n.set_snapshots(SNAP)
    buses={'KGN':dict(x=-76.79,y=17.97,pf=.40),'OH':dict(x=-76.95,y=17.94,pf=.15),
           'MP':dict(x=-77.25,y=17.97,pf=.15),'MB':dict(x=-77.92,y=18.47,pf=.30)}
    for b,d in buses.items(): n.add("Bus",b,carrier="AC",x=d['x'],y=d['y'])
    for s,d,cap,eta in [('KGN','OH',300,.990),('OH','MP',200,.985),('MP','MB',180,.975)]:
        n.add("Link",f"tx_{s}_{d}",bus0=s,bus1=d,p_nom=cap,efficiency=eta)
        n.add("Link",f"tx_{d}_{s}",bus0=d,bus1=s,p_nom=cap,efficiency=eta)
    # Thermal fleet
    n.add("Generator","JM_jep",bus="OH",carrier="lng",p_nom=190,marginal_cost=105,p_min_pu=.40)
    n.add("Generator","JM_oh_hfo",bus="OH",carrier="hfo",p_nom=120,marginal_cost=240,p_min_pu=.35)
    n.add("Generator","JM_hb",bus="KGN",carrier="hfo",p_nom=150,marginal_cost=235,p_min_pu=.30)
    n.add("Generator","JM_jppc",bus="KGN",carrier="diesel",p_nom=60,marginal_cost=275)
    n.add("Generator","JM_bogue",bus="MB",carrier="gas",p_nom=120,marginal_cost=170,p_min_pu=.30)
    n.add("Generator","JM_rock",bus="KGN",carrier="diesel",p_nom=60,marginal_cost=260)
    # Existing RE
    n.add("Generator","JM_wig",bus="MP",carrier="wind",p_nom=100,marginal_cost=0,p_max_pu=wind_p(.30,62))
    hcf=np.clip(.40+.10*np.cos(2*np.pi*(np.arange(H)//24-240)/365)+ar1(H,.88,.05,65),.15,.70)
    n.add("Generator","JM_hyd",bus="MP",carrier="hydro",p_nom=29,marginal_cost=2,p_max_pu=hcf)
    n.add("Generator","JM_sol_k",bus="KGN",carrier="solar",p_nom=37,marginal_cost=0,p_max_pu=solar_p(.21,17.97,63))
    n.add("Generator","JM_sol_m",bus="MP",carrier="solar",p_nom=20,marginal_cost=0,p_max_pu=solar_p(.21,18.0,64))
    # Extendable RE
    n.add("Generator","JM_sol1",bus="MP",carrier="solar",p_nom_extendable=True,p_nom_max=400,
          capital_cost=acap(1100,12,25,r),marginal_cost=.5,p_max_pu=solar_p(.21,18.0,66))
    n.add("Generator","JM_wnd1",bus="MB",carrier="wind",p_nom_extendable=True,p_nom_max=300,
          capital_cost=acap(1600,35,20,r),marginal_cost=1.,p_max_pu=wind_p(.30,67))
    n.add("Generator","JM_sol2",bus="OH",carrier="solar",p_nom_extendable=True,p_nom_max=150,
          capital_cost=acap(1100,12,25,r),marginal_cost=.5,p_max_pu=solar_p(.20,17.94,68))
    # Storage
    add_bess(n,"KGN","JMk",500,r); add_bess(n,"OH","JMo",300,r); add_h2(n,"KGN","JM",30,r)
    for b in buses: n.add("Generator",f"JM_{b}_v",bus=b,carrier="load_shed",p_nom=1e4,marginal_cost=2500)
    for b,d in buses.items():
        ld,_=load_p(650*d['pf'],70+list(buses.keys()).index(b))
        n.add("Load",f"{b}_ld",bus=b,p_set=ld*1.08)
    _,kTa=load_p(650*.40,70)
    _,inf,flx=dc_load(15,1.4,.30,kTa)
    n.add("Load","JM_dci",bus="KGN",p_set=inf)
    n.add("Load","JM_dcf",bus="KGN",p_set=flx)
    add_bess(n,"KGN","JMdc",15*1.4*4,r,btm=True)
    return n

# ── Extraction ──
def extract(n,name):
    re_s={'solar','wind','geothermal','hydro'}
    tot=sum(n.generators_t.p[g].sum() for g in n.generators.index if n.generators.loc[g,'carrier']!='load_shed')
    reg=sum(n.generators_t.p[g].sum() for g in n.generators.index if n.generators.loc[g,'carrier'] in re_s)
    rf=reg/tot if tot>0 else 0
    def ec(c): return sum(n.generators.loc[g,'p_nom_opt'] for g in n.generators.index
                          if n.generators.loc[g,'carrier']==c and n.generators.loc[g,'p_nom_extendable'])
    bess=sum(max(0,n.stores.loc[s,'e_nom_opt']) for s in n.stores.index
             if 'bess' in s and n.stores.loc[s,'e_nom_extendable'])
    btm=sum(max(0,n.stores.loc[s,'e_nom_opt']) for s in n.stores.index
            if 'btms' in s and n.stores.loc[s,'e_nom_extendable'])
    h2=sum(n.links.loc[l,'p_nom_opt'] for l in n.links.index
           if 'elz' in l and n.links.loc[l,'p_nom_extendable'])
    co2=sum(n.generators_t.p[g].sum()*EF.get(n.generators.loc[g,'carrier'],0)
            for g in n.generators.index)/1000
    voll=sum(n.generators_t.p[g].sum() for g in n.generators.index
             if n.generators.loc[g,'carrier']=='load_shed')
    cost=n.objective/1e6/FRAC if hasattr(n,'objective') and n.objective else 0
    co2=co2/FRAC
    return dict(case=name,cost=cost,re_frac=rf,sol_mw=ec('solar'),wnd_mw=ec('wind'),
                bess_mwh=bess,btm_mwh=btm,h2_mw=h2,co2_kt=co2,voll=voll)

# ── Post-hoc DRO ──
def dro_calc():
    cats={'C1':(.35,.15,24),'C2':(.25,.30,48),'C3':(.20,.50,72),'C4':(.15,.70,120),'C5':(.05,.90,240)}
    islands={'Trinidad':(.3,30,5),'Jamaica':(.8,100,15)}
    eps_v=np.linspace(0,.20,7); res={}
    for isl,(s,bess,dc) in islands.items():
        r={}
        for eps in eps_v:
            us=0
            for _,(p,g,h) in cats.items():
                pp=np.clip(p*s+eps*(2*g-.5),.001,.999)
                dem=dc*h; sup=dc*(1-g)*.5*h+bess*(1-g*.3)
                us+=pp*max(0,dem-sup)
            r[round(eps,3)]=max(0,1-us/(dc*8760))
        res[isl]=r
    return res

# ══════════════════════════════════════════════════════
# FIGURES
# ══════════════════════════════════════════════════════
def savefig(fig,nm):
    for e in ['pdf','png']: fig.savefig(f'{FDIR}/{nm}.{e}',dpi=300,bbox_inches='tight')
    plt.close()

def fig1a_jamaica():
    """High-res Jamaica geoplot with 4-bus JPS topology."""
    fig,ax=plt.subplots(figsize=(6.5,3.8))
    ax.set_xlim(-78.5,-76.0); ax.set_ylim(17.55,18.65)
    ax.set_facecolor('#D6EAF8'); ax.set_aspect('equal')
    jm=[(-78.4,18.45),(-78.3,18.15),(-77.9,17.75),(-77.4,17.7),(-76.8,17.7),
        (-76.3,17.78),(-76.18,17.88),(-76.18,18.12),(-76.3,18.25),(-76.45,18.22),
        (-76.55,18.38),(-77.0,18.45),(-77.4,18.5),(-77.7,18.45),(-78.0,18.38),(-78.4,18.45)]
    ax.add_patch(Polygon(jm,closed=True,fc='#F0EBD8',ec='#777',lw=.8,zorder=2))
    # Context towns
    for nm,la,lo in [('Spanish Town',17.99,-76.95),('Mandeville',18.04,-77.50),
                      ('Ocho Rios',18.41,-77.10),('Port Antonio',18.18,-76.45)]:
        ax.plot(lo,la,'.',color='#999',ms=4,zorder=3)
        ax.text(lo+.06,la+.03,nm,fontsize=4,color='#888')
    # 138kV lines
    segs=[((-76.79,17.97),(-76.95,17.94),'300 MW\n20 km'),
           ((-76.95,17.94),(-77.25,17.97),'200 MW\n40 km'),
           ((-77.25,17.97),(-77.92,18.47),'180 MW\n100 km')]
    for (x1,y1),(x2,y2),lbl in segs:
        ax.plot([x1,x2],[y1,y2],color='#D4760A',lw=2.5,alpha=.7,zorder=4,solid_capstyle='round')
        mx,my=(x1+x2)/2,(y1+y2)/2
        ax.text(mx-.22,my+.08,lbl,fontsize=3.5,color='#D4760A',style='italic',ha='center')
    # Nodes
    nodes=[('Kingston',17.97,-76.79,'15 MW DC\nHunts Bay 150 MW\nJPPC 60 MW\nContent Solar 37 MW','#E8963E',150,'right'),
           ('Old Harbour',17.94,-76.95,'JEP 190 MW LNG\nLegacy HFO 120 MW\nBrownfield solar\npotential 150 MW','#F4A300',90,'left'),
           ('May Pen',17.97,-77.25,'Wigton Wind 100 MW\nHydro 29 MW\nEight Rivers 20 MW\nSolar potential 400 MW','#F4A300',90,'left'),
           ('Montego Bay',18.47,-77.92,'Bogue GT 120 MW\nWind potential\n300 MW\nTourism load centre','#F4A300',110,'right')]
    for nm,la,lo,det,col,sz,side in nodes:
        ax.scatter(lo,la,s=sz,c=col,edgecolors='k',lw=1,zorder=6)
        xo=.18 if side=='right' else -.18
        yo=-.25 if la<18.2 else .15
        ax.annotate(f'{nm}\n{det}',(lo,la),xytext=(lo+xo,la+yo),fontsize=4,fontweight='bold',
                   va='top' if yo<0 else 'bottom',ha='left' if side=='right' else 'right',
                   bbox=dict(boxstyle='round,pad=.15',fc='white',alpha=.92,ec=col,lw=.6),
                   arrowprops=dict(arrowstyle='->',color=col,lw=.7),zorder=7)
    # DC marker
    ax.scatter(-76.79,17.97,s=30,c='red',marker='*',zorder=8)
    # Fibre to Miami
    ax.annotate('To Miami (SCFS/JFS)\n<30 ms RTT',xy=(-78.45,18.6),fontsize=3.5,color='#6C757D',
               style='italic',ha='left')
    ax.annotate('',xy=(-78.5,18.6),xytext=(-78.0,18.45),arrowprops=dict(arrowstyle='->',color='#6C757D',lw=.7,ls='--'))
    leg=[Line2D([0],[0],marker='o',color='w',markerfacecolor='#E8963E',ms=9,mec='k',mew=.6,label='Bus with DC (Kingston)'),
         Line2D([0],[0],marker='o',color='w',markerfacecolor='#F4A300',ms=7,mec='k',mew=.6,label='138 kV bus'),
         Line2D([0],[0],color='#D4760A',lw=2.5,label='138 kV transmission')]
    ax.legend(handles=leg,loc='lower right',fontsize=5,framealpha=.9)
    ax.set_xlabel('Longitude (°W)',fontsize=7); ax.set_ylabel('Latitude (°N)',fontsize=7)
    ax.tick_params(labelsize=6); ax.grid(alpha=.12,ls='--')
    ax.set_title('Case B: Jamaica — 4-Bus JPS Transmission Topology',fontsize=9,fontweight='bold')
    fig.tight_layout(); savefig(fig,'fig1a_jamaica'); print("  Fig1a ok")

def fig1b_trinidad():
    """High-res Trinidad geoplot with Brechin Castle and Point Lisas."""
    fig,ax=plt.subplots(figsize=(6.5,3.8))
    ax.set_xlim(-62.1,-60.4); ax.set_ylim(9.95,10.95)
    ax.set_facecolor('#D6EAF8'); ax.set_aspect('equal')
    tt=[(-61.95,10.05),(-61.65,10.0),(-61.0,10.03),(-60.92,10.08),(-60.85,10.15),
        (-60.83,10.35),(-60.88,10.48),(-60.95,10.58),(-61.05,10.68),(-61.4,10.72),
        (-61.62,10.72),(-61.85,10.68),(-61.92,10.55),(-61.93,10.35),(-61.95,10.15),(-61.95,10.05)]
    ax.add_patch(Polygon(tt,closed=True,fc='#F0EBD8',ec='#777',lw=.8,zorder=2))
    # Towns
    for nm,la,lo in [('Port of Spain',10.66,-61.51),('San Fernando',10.28,-61.47),
                      ('Chaguanas',10.52,-61.41),('Arima',10.64,-61.28),
                      ('Scarborough\n(Tobago)',11.18,-60.73)]:
        ax.plot(lo,la,'.',color='#999',ms=4,zorder=3)
        ax.text(lo+.04,la+.03,nm,fontsize=4,color='#888')
    # Tobago (small)
    tb=[(-60.85,11.10),(-60.50,11.10),(-60.48,11.22),(-60.55,11.30),(-60.80,11.25),(-60.85,11.10)]
    ax.add_patch(Polygon(tb,closed=True,fc='#F0EBD8',ec='#777',lw=.5,zorder=2))

    # Brechin Castle Solar (near Couva, NE of Point Lisas)
    bc_la,bc_lo=10.42,-61.38
    ax.scatter(bc_lo,bc_la,s=180,c='#F4A300',edgecolors='k',lw=1,zorder=6,marker='D')
    ax.annotate('Brechin Castle Solar\n92 MWac (bp/Shell/NGC)\n186 ha, commissioned 2025\nCaribbean\'s largest utility-scale PV',
               (bc_lo,bc_la),xytext=(bc_lo+.35,bc_la+.25),fontsize=4.5,fontweight='bold',
               bbox=dict(boxstyle='round,pad=.15',fc='white',alpha=.92,ec='#F4A300',lw=.6),
               arrowprops=dict(arrowstyle='->',color='#F4A300',lw=.8),zorder=7)
    # Point Lisas Industrial Estate (proposed DC site)
    pl_la,pl_lo=10.38,-61.47
    ax.scatter(pl_lo,pl_la,s=140,c='#2E86AB',edgecolors='k',lw=1,zorder=6,marker='s')
    ax.annotate('Point Lisas\nIndustrial Estate\n5 MW DC (proposed)\nHeavy industrial zoning\nExisting T&TEC substation',
               (pl_lo,pl_la),xytext=(pl_lo-.55,pl_la-.30),fontsize=4.5,fontweight='bold',
               bbox=dict(boxstyle='round,pad=.15',fc='white',alpha=.92,ec='#2E86AB',lw=.6),
               arrowprops=dict(arrowstyle='->',color='#2E86AB',lw=.8),zorder=7)
    # Gas fleet (conceptual, PowerGen)
    pg_la,pg_lo=10.28,-61.43
    ax.scatter(pg_lo,pg_la,s=60,c='#8B8B8B',edgecolors='k',lw=.6,zorder=5)
    ax.annotate('PowerGen fleet\n~1,800 MW (NGC gas)',
               (pg_lo,pg_la),xytext=(pg_lo+.30,pg_la-.15),fontsize=3.8,
               bbox=dict(boxstyle='round,pad=.1',fc='white',alpha=.85,ec='#888',lw=.4),
               arrowprops=dict(arrowstyle='->',color='#888',lw=.5),zorder=7)
    # 2.8km grid connection line (Brechin to substation)
    ax.plot([bc_lo,bc_lo-.06],[bc_la,bc_la-.03],color='#D4760A',lw=1.5,ls='--',alpha=.7,zorder=4)
    ax.text(bc_lo-.08,bc_la-.04,'2.8 km\n138 kV',fontsize=3,color='#D4760A',style='italic')
    # Submarine cables
    ax.annotate('Americas II cable\nSCFS to Miami',xy=(-60.45,10.85),fontsize=3.5,color='#6C757D',style='italic')

    leg=[Line2D([0],[0],marker='D',color='w',markerfacecolor='#F4A300',ms=9,mec='k',mew=.6,label='Brechin Castle Solar (92 MW)'),
         Line2D([0],[0],marker='s',color='w',markerfacecolor='#2E86AB',ms=8,mec='k',mew=.6,label='Proposed DC site (5 MW)'),
         Line2D([0],[0],marker='o',color='w',markerfacecolor='#8B8B8B',ms=6,mec='k',mew=.4,label='Thermal generation')]
    ax.legend(handles=leg,loc='upper left',fontsize=5,framealpha=.9)
    ax.set_xlabel('Longitude (°W)',fontsize=7); ax.set_ylabel('Latitude (°N)',fontsize=7)
    ax.tick_params(labelsize=6); ax.grid(alpha=.12,ls='--')
    ax.set_title('Case A: Trinidad & Tobago — Single-Bus with Brechin Castle Solar',fontsize=9,fontweight='bold')
    fig.tight_layout(); savefig(fig,'fig1b_trinidad'); print("  Fig1b ok")

def fig2_results(ra,rb):
    fig,axes=plt.subplots(1,4,figsize=(8,2.5))
    cs=['A: Trinidad','B: Jamaica']; co=['#2E86AB','#F4A300']
    metrics=[
        ([ra['re_frac']*100,rb['re_frac']*100],'RE (%)','(a) RE Penetration'),
        ([ra['cost'],rb['cost']],'M USD/yr','(b) System Cost'),
        ([ra['co2_kt'],rb['co2_kt']],'kt CO₂/yr','(c) Emissions'),
        ([ra['sol_mw']+ra['wnd_mw'],rb['sol_mw']+rb['wnd_mw']],'MW','(d) New RE Capacity')]
    for i,(v,yl,tt) in enumerate(metrics):
        bars=axes[i].bar(cs,v,color=co,alpha=.85,edgecolor='k',lw=.5)
        for b,val in zip(bars,v):
            axes[i].text(b.get_x()+b.get_width()/2,b.get_height()+max(v)*.03,f'{val:.0f}',ha='center',fontsize=5.5)
        axes[i].set_ylabel(yl,fontsize=6); axes[i].set_title(tt,fontsize=6.5,fontweight='bold')
        axes[i].grid(axis='y',alpha=.3); axes[i].tick_params(labelsize=5.5)
    fig.tight_layout(); savefig(fig,'fig2_results'); print("  Fig2 ok")

# ══════════════════════════════════════════════════════
if __name__=='__main__':
    t0=time.time()
    print("="*55); print("PyPSA DC-RE Caribbean SIDS (v4 production)"); print("="*55)
    print("\n[FIG] Geoplots...")
    fig1a_jamaica(); fig1b_trinidad()
    print("\n[OPT] Case A: Trinidad...")
    na=case_a(); na.optimize(solver_name='highs',solver_options={'time_limit':120})
    ra=extract(na,'Case A: Trinidad')
    print(f"  Cost={ra['cost']:.0f} RE={ra['re_frac']:.1%} Sol={ra['sol_mw']:.0f} Wnd={ra['wnd_mw']:.0f} BESS={ra['bess_mwh']:.0f} BTM={ra['btm_mwh']:.0f}")
    print("\n[OPT] Case B: Jamaica (4-bus)...")
    nb=case_b(); nb.optimize(solver_name='highs',solver_options={'time_limit':120})
    rb=extract(nb,'Case B: Jamaica')
    print(f"  Cost={rb['cost']:.0f} RE={rb['re_frac']:.1%} Sol={rb['sol_mw']:.0f} Wnd={rb['wnd_mw']:.0f} BESS={rb['bess_mwh']:.0f} BTM={rb['btm_mwh']:.0f}")
    print("\n[FIG] Results..."); fig2_results(ra,rb)
    print("\n[POST] DRO..."); dro=dro_calc()
    el=time.time()-t0
    print(f"\n{'='*55}\nDONE in {el:.0f}s\n{'='*55}")
    for r in [ra,rb]:
        print(f"  {r['case']:<20} Cost={r['cost']:.0f} RE={r['re_frac']:.1%} Sol={r['sol_mw']:.0f} Wnd={r['wnd_mw']:.0f} BESS={r['bess_mwh']:.0f} BTM={r['btm_mwh']:.0f} CO2={r['co2_kt']:.0f}kt")
    rj={'CaseA':ra,'CaseB':rb,'dro':dro}
    with open(f'{FDIR}/results.json','w') as f: json.dump(rj,f,indent=2,default=str)
