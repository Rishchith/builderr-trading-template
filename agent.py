"""
BUILDERR ROUND 1 — agent.py v7 EMERGENCY FIX (June 30, 2026)
================================================================
WHAT WENT WRONG WITH v6:
  v6 made a hard directional bet (IWM/XLF/XLI 1.4-1.6x boost) on rotation
  continuing. The market REVERSED Monday — Mag7 snapped back hard
  (Nasdaq +2.25%, GOOGL +4.96%, TSLA +8.45%) while the rotation trade
  stalled (Russell 2000 only +0.01-0.07%, basically flat).
  
  LESSON: don't make large directional sector bets based on ONE week's
  data. The "rotation" was actually quarter-end window dressing + 
  short covering in beaten-down names — NOT a durable trend.
  Source confirms this: "A bounce driven by short-covering and 
  quarter-end positioning... is not an indication of fundamental health."

CURRENT SITUATION (June 30, 2026 — live data):
  • Dow closed ABOVE 52,000 for first time — new all-time high
  • S&P 500 at 7,440 — also pushing higher
  • Nasdaq +2.25% Monday, +1.25-2.1% Tuesday — STRONG broad rally
  • VIX down to ~16.6-17.6 — fear receding fast
  • US-Iran ceasefire holding, Strait of Hormuz reopened — geopolitical 
    risk DOWN significantly
  • GOOGL +4.96% Monday on Dow inclusion, still strong Tuesday
  • TSLA +8.45% Monday — huge AI/EV momentum
  • Memory/chip stocks (MU, SMH) recovering — Korean competitors 
    pledging new investment, easing supply panic
  • KEY: BROAD-BASED rally, NOT narrow rotation — tech, comm services,
    consumer discretionary ALL leading together
  • Jul 1: ADP, ISM Manufacturing, JOLTS — all this week
  • Jul 2: NONFARM PAYROLLS — final scoring catalyst, then round ends
  • Jul 3: Market CLOSED (July 4th observed)
  • "Best quarter for S&P 500 and Nasdaq in six years" despite Iran war

CRITICAL STRATEGY CHANGE — RISK MANAGEMENT FIRST:
  v6's mistake: concentrated 1.6x/0.5x bet on ONE narrative (rotation)
  v7's fix: BROAD-BASED diversification across ALL current winners,
            NO single-direction mega-bet, narrower boost spread (1.15x-0.85x)
            This way if the "today's winner" rotates again, we're not
            wiped out — we're diversified across multiple confirmed winners.

  Trade count fix RETAINED (this part worked): daily rebalance,
  low MIN_TRADE_PCT, tight drift threshold → still generates 10-15 trades
  
  Position sizing: SAFER. Max weight 0.20 (was 0.24-0.26). 
  Beta gross 1.15x (was 1.30-1.40x). This is now a RECOVERY-MODE agent:
  prioritize not losing more, while still capturing the broad rally.
"""

from __future__ import annotations
from math import sqrt
from statistics import mean, pstdev
from typing import Any

# ── UNIVERSE — broad market, NOT narrow rotation bet ──────────────────────────
RISK_CANDIDATES = (
    # Broad market anchors — the rally is broad-based, not narrow
    "SPY", "QQQ", "DIA",

    # Mega-cap tech — confirmed snapback leaders (GOOGL +4.96%, TSLA +8.45%)
    "GOOGL", "TSLA", "META", "AMZN",

    # Communication / Consumer — biggest gainers Tuesday (XLC +3.1%, XLY +2.7%)
    "XLC", "XLY",

    # Tech broadly — XLK +1.7-2.18%
    "XLK", "SMH",

    # Still include rotation names but smaller weight — don't abandon entirely
    "XLF", "XLI", "XLV", "IWM",

    # Memory recovering
    "MU",
)

# NARROWER boost spread — 1.15x to 0.85x (was 1.6x to 0.5x in v6)
# This is the key fix: no more concentrated directional bets
SECTOR_BOOST = {
    # Confirmed broad rally leaders — modest boost only
    "GOOGL": 1.15,   # Dow inclusion + still gaining
    "TSLA":  1.15,   # huge momentum but volatile — capped boost
    "XLC":   1.15,   # communication services leading
    "XLY":   1.12,   # consumer discretionary leading
    "XLK":   1.10,   # tech broadly recovering
    "META":  1.08,
    "AMZN":  1.05,
    "SMH":   1.05,   # semis recovering as Korea panic eases

    # Broad market — neutral, reliable
    "QQQ":   1.05,
    "SPY":   1.00,
    "DIA":   1.00,   # at all-time highs, steady

    # Rotation names — REDUCED conviction (lesson learned), not abandoned
    "XLF":   0.95,
    "XLI":   0.95,
    "XLV":   0.90,
    "IWM":   0.85,   # rotation stalled — significantly reduced from 1.6x

    "MU":    0.90,   # recovering but Korea oversupply concern lingers
}

# Defensive — unchanged, still no XLU (rate risk)
DEFENSIVE_CRASH   = (("XLV", 0.40), ("XLP", 0.35), ("GLD", 0.25))
DEFENSIVE_RISKOFF = (("XLV", 0.30), ("XLP", 0.25), ("GLD", 0.25), ("XLF", 0.20))
CAUTIOUS_DEF      = (("XLV", 0.08), ("XLP", 0.07))

BETA_MULTIPLE: dict[str, float] = {
    "QLD": 2.0, "SSO": 2.0, "TQQQ": 3.0, "SOXL": 3.0,
    "UPRO": 3.0, "SPXL": 3.0,
}

# ── TUNING — RECOVERY MODE: safer sizing, same trade frequency ───────────────
REBALANCE_DAYS  = 1        # keep daily — this part worked
MAX_WEIGHT      = 0.20     # REDUCED from 0.24-0.26 — no more concentration risk
DRIFT_LIM       = 0.10     # keep sensitive — drives trade count
MAX_BETA_GROSS  = 1.15     # REDUCED from 1.30-1.40 — much safer
MIN_TRADE_PCT   = 0.005    # keep low — drives trade count
TOP_N_RISKON    = 7        # MORE diversified (was 5) — spread risk wider
DEPLOY_PCT      = 0.90     # slightly less than 95-97% — keep some cash buffer
DD_STOP         = 0.05     # 5% drawdown stop — tighter than v6's 6%

VOL_CAUTION     = 0.26
CRASH_DROP_3BAR = -0.025
CRASH_VOL_RATIO = 1.6

_peak_equity: float = 0.0
_last_rebal_date: str | None = None


# ── Utilities (unchanged) ─────────────────────────────────────────────────────
def closes(bars):
    if not bars: return []
    out = []
    for b in bars:
        try: c = float(b["close"])
        except: return []
        if c <= 0: return []
        out.append(c)
    return out

def sma(v, n): return mean(v[-n:]) if len(v) >= n else None
def mom(v, n): return (v[-1]/v[-(n+1)]-1.0) if len(v)>n and v[-(n+1)]>0 else None
def rvol(v, n):
    if len(v) <= n: return None
    w = v[-(n+1):]
    rs = [w[i]/w[i-1]-1.0 for i in range(1,len(w)) if w[i-1]>0]
    return pstdev(rs)*sqrt(252.0) if len(rs)>=4 else None

def cur_pos(ps):
    out = {}
    for r in (ps.get("positions") or []):
        t = str(r.get("ticker","")).upper()
        if not t: continue
        try: qty=float(r.get("quantity",0)); cost=float(r.get("avg_cost",0))
        except: continue
        if qty<=0: continue
        e=out.setdefault(t,{"quantity":0.0,"avg_cost":cost})
        e["quantity"]+=qty
    return out

def tot_equity(ps, cash):
    try: total=float(ps.get("cash",cash))
    except: total=float(cash or 0)
    lp=ps.get("last_prices",{}) or {}
    for t,p in cur_pos(ps).items():
        try: price=float(lp.get(t,p["avg_cost"]))
        except: price=p["avg_cost"]
        total+=p["quantity"]*max(price,0)
    return max(total,0)

def mkt_prices(ms):
    out={}
    for t,bars in ms.items():
        cs=closes(bars)
        if cs: out[t.upper()]=cs[-1]
    return out

def bar_date(ms):
    bars=ms.get("SPY") or ms.get("QQQ") or []
    if not bars: return None
    ts=bars[-1].get("ts")
    return str(ts)[:10] if ts is not None else str(len(bars))

def days_since(ms):
    if _last_rebal_date is None: return None
    bars=ms.get("SPY") or ms.get("QQQ") or []
    dates=[str(b.get("ts",i))[:10] for i,b in enumerate(bars)]
    if not dates or _last_rebal_date not in dates: return None
    return len(dates)-dates.index(_last_rebal_date)-1

def drifted(ps, eq):
    if eq<=0: return False
    lp=ps.get("last_prices",{}) or {}
    for t,p in cur_pos(ps).items():
        try: price=float(lp.get(t,p["avg_cost"]))
        except: price=p["avg_cost"]
        if price>0 and (p["quantity"]*price/eq)>DRIFT_LIM: return True
    return False

# ── Cap enforcement ────────────────────────────────────────────────────────────
def cap(w):
    c={t:min(max(v,0),MAX_WEIGHT) for t,v in w.items() if v>0}
    bg=sum(v*BETA_MULTIPLE.get(t,1.0) for t,v in c.items())
    if bg>MAX_BETA_GROSS:
        sc=MAX_BETA_GROSS/bg; c={t:v*sc for t,v in c.items()}
    return {t:round(v,6) for t,v in c.items() if v>0.001}

# ── Regime detection ───────────────────────────────────────────────────────────
def regime(ms):
    spy=closes(ms.get("SPY")); qqq=closes(ms.get("QQQ"))
    if len(spy)<30 or len(qqq)<30: return "risk_off"
    n=min(50,len(spy)-1)
    spy50=sma(spy,n); qqq50=sma(qqq,min(n,len(qqq)-1))
    qv20=rvol(qqq,min(20,len(qqq)-2))
    qm20=mom(qqq,min(20,len(qqq)-2))
    sm20=mom(spy,min(20,len(spy)-2))
    if any(x is None for x in (spy50,qqq50,qv20)): return "risk_off"

    qm3=mom(qqq,min(3,len(qqq)-2))
    if qm3 is not None and qm3<CRASH_DROP_3BAR: return "crash_bail"
    if len(qqq)>=24:
        v3=rvol(qqq,3); v20=rvol(qqq,20)
        if v3 and v20 and v20>0 and v3>CRASH_VOL_RATIO*v20: return "crash_bail"

    if spy[-1]<spy50 and (qm20 is not None and qm20<-0.05):
        return "risk_off"

    if qv20>=VOL_CAUTION: return "cautious"
    if qm20 is not None and qm20<0: return "cautious"
    if sm20 is not None and sm20<0: return "cautious"
    return "risk_on"

# ── Scoring — broad-based, no narrow directional bet ──────────────────────────
def score_universe(ms):
    """
    Balanced short+medium momentum. Boost spread NARROWED to 1.15x-0.85x
    (was 1.6x-0.5x) — this is the core fix. We still favour confirmed
    winners (GOOGL, TSLA, XLC, XLY, XLK) but don't bet the farm on them.
    TOP_N raised to 7 for natural diversification.
    """
    scored = []
    for t in RISK_CANDIDATES:
        v = closes(ms.get(t))
        if len(v) < 10: continue
        m10  = mom(v, min(10, len(v)-2))
        m5   = mom(v, min(5,  len(v)-2))
        m2   = mom(v, min(2,  len(v)-2))
        n_s  = min(20, len(v)-1)
        s20  = sma(v, n_s)
        v10  = rvol(v, min(10, len(v)-2))
        if any(x is None for x in (m5, s20)):
            continue
        v10  = v10 or 0.20
        gap  = v[-1]/s20 - 1.0
        m10  = m10 or m5
        m2   = m2 or m5
        # Balanced — no single factor dominates
        raw  = (0.30*m5 + 0.25*m10 + 0.25*gap + 0.20*m2)
        boosted = raw * SECTOR_BOOST.get(t, 1.0)
        scored.append((boosted, t, max(v10, 0.01)))
    scored.sort(reverse=True)
    return scored

def inv_vol_w(cands, budget):
    if not cands: return {}
    ivs=[1.0/max(v,1e-6) for _,_,v in cands]
    tot=sum(ivs)
    if tot<=0:
        n=len(cands)
        return {t:min(budget/n,MAX_WEIGHT) for _,t,_ in cands}
    return {t:min(budget*iv/tot,MAX_WEIGHT)
            for (_,t,_),iv in zip(cands,ivs)}

# ── Target weights ─────────────────────────────────────────────────────────────
def target_weights(ms, drawdown: float = 0.0):
    r = regime(ms)
    if drawdown > DD_STOP and r == "risk_on":
        r = "cautious"

    if r == "crash_bail":
        return cap({t:w for t,w in DEFENSIVE_CRASH if closes(ms.get(t))})
    if r == "risk_off":
        return cap({t:w for t,w in DEFENSIVE_RISKOFF if closes(ms.get(t))})

    scored = score_universe(ms)
    pos = [(s,t,v) for s,t,v in scored if s > 0]

    if r == "cautious":
        winners = pos[:5]
        if not winners:
            return cap({t:w for t,w in DEFENSIVE_RISKOFF if closes(ms.get(t))})
        cdef={t:w for t,w in CAUTIOUS_DEF if closes(ms.get(t))}
        rb=min(0.60,1.0-sum(cdef.values()))
        return cap({**cdef, **inv_vol_w(winners,rb)})

    winners = pos[:TOP_N_RISKON]
    if not winners:
        return cap({t:w for t,w in DEFENSIVE_RISKOFF if closes(ms.get(t))})
    return cap(inv_vol_w(winners, DEPLOY_PCT))

# ── Orders ─────────────────────────────────────────────────────────────────────
def build_orders(targets, positions, eq, prices, cash):
    if eq<=0: return []
    min_t=eq*MIN_TRADE_PCT
    orders=[]; sell_proc=0.0

    for t,p in positions.items():
        price=prices.get(t)
        if not price or price<=0: continue
        qty=p["quantity"]; cv=qty*price
        tv=eq*targets.get(t,0.0)
        if t not in targets:
            sq=int(qty)
            if sq>0 and cv>=min_t:
                orders.append({"ticker":t,"side":"sell","quantity":sq})
                sell_proc+=sq*price
        elif tv-cv<-min_t:
            sq=min(int(abs(tv-cv)/price),int(qty))
            if sq>0:
                orders.append({"ticker":t,"side":"sell","quantity":sq})
                sell_proc+=sq*price

    spendable=max(float(cash),0.0)+sell_proc*0.98
    for t,w in sorted(targets.items(),key=lambda x:-x[1]):
        price=prices.get(t)
        if not price or price<=0: continue
        cv=positions.get(t,{}).get("quantity",0.0)*price
        tv=eq*w
        if tv-cv<min_t: continue
        bq=int(min(tv-cv,spendable)/price)
        if bq>0:
            orders.append({"ticker":t,"side":"buy","quantity":bq})
            spendable-=bq*price
    return orders[:45]

# ── Entry point ────────────────────────────────────────────────────────────────
def decide(market_state, portfolio_state, cash):
    """
    RECOVERY MODE: broad-based diversification, no concentrated directional
    bets. Daily rebalance retained for trade frequency. Tighter risk caps
    (beta 1.15x, max weight 0.20, 7 positions) after v6's narrow rotation
    bet underperformed when the market snapped back to mega-cap tech.
    """
    global _last_rebal_date, _peak_equity

    if not market_state: return []
    today=bar_date(market_state)
    if today is None: return []

    eq=tot_equity(portfolio_state,cash)
    if eq>_peak_equity: _peak_equity=eq
    dd=(_peak_equity-eq)/_peak_equity if _peak_equity>0 else 0.0

    dsince=days_since(market_state)
    drift=drifted(portfolio_state,eq)
    r=regime(market_state)

    should_rebal=(
        _last_rebal_date is None
        or dsince is None
        or dsince>=REBALANCE_DAYS
        or drift
        or r=="crash_bail"
    )
    if not should_rebal: return []

    tgts=target_weights(market_state,dd)
    if not tgts: return []

    prices=mkt_prices(market_state)
    pos=cur_pos(portfolio_state)
    orders=build_orders(tgts,pos,eq,prices,cash)
    if orders: _last_rebal_date=today
    return orders
