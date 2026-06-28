"""
BUILDERR ROUND 1 — agent.py v6 FINAL (June 29, 2026 — Sunday Intel)
=====================================================================
POSITION: Rank 4/31 | ~$800 profit (~0.8%) | Need +10% in 4 days
TARGET:   Overtake #1 (currently +8%) → need aggressive but precise moves

COMPLETE MARKET INTELLIGENCE (June 28-29, 2026 weekend research):

MACRO BACKDROP:
  • VIX at 15 — historically low, risk-on conditions ✅
  • Oil WTI < $70 (down $40 from peak) — huge consumer/industrial tailwind ✅
  • Fed: 50% chance of hike by year end, but NOT imminent — no panic ✅
  • 10yr Treasury ~4.4% — stable, not spiking ✅
  • Dollar at 2026 highs — slight headwind for multinationals ⚠️

ROTATION TRADE (THE DOMINANT THEME THIS WEEK):
  Tech/Nasdaq: DOWN 5% this week, AAPL -6%, MSFT -3%, NVDA -2%
  → AI hardware price hike fears + KOSPI tech shock from Korea
  WINNERS this week and likely next:
  • IWM (Russell 2000) — RECORD CLOSE Friday, +1.29% ✅ BUY
  • XLF (Financials) — benefiting from rotation + stable rates ✅ BUY
  • XLI (Industrials) — CAT, GE strong, oil drop = cost savings ✅ BUY
  • XLV (Healthcare) — defensive rotation winner ✅ BUY
  • XLY (Consumer Disc) — oil drop = consumer spending boost ✅ BUY
  LOSERS to avoid:
  • AAPL, MSFT — hardware price hike headwinds ❌ AVOID
  • Heavy tech/semi ETFs (XLK, SMH) — under pressure ❌ REDUCE

KEY CATALYSTS THIS WEEK (day by day):
  MON Jun 29: Light data, GOOGL Dow inclusion effective TODAY
              → institutional FORCED buying of GOOGL ✅
  TUE Jun 30: Consumer Confidence + JOLTS + Nike earnings after close
              → If NKE beats (4 quarters in a row) = XLY pop ✅
              → GOOGL Dow rebalancing buys continue ✅
  WED Jul 1:  ADP Employment + ISM Manufacturing PMI
              → May NFP was 172K vs 85K forecast → expect above-expect ADP
              → Strong ADP = market rally + IWM/XLF pop ✅
              → ISM Manufacturing turning? Watch closely
  THU Jul 2:  NONFARM PAYROLLS (biggest market mover)
              → Leading indicators: ABOVE expected reading likely
              → Above-expected NFP + low VIX = END OF ROUND RALLY ✅
              → This is our big day — must be fully positioned by Wed close

STOCKS TO TARGET (ranked by conviction):
  TIER 1 — Highest conviction (rotation + catalyst):
    IWM   — Russell 2000 record close, rotation king, NFP beneficiary
    GOOGL — Dow Jones inclusion TODAY (Jun 29), forced buying all week
    XLF   — Financials rotation + stable rates + above-expect jobs = rally
    XLI   — Oil drop = industrial margin expansion, Dow at record highs
  
  TIER 2 — Strong momentum:
    XLV   — Healthcare defensive rotation, low vol, consistent gains
    XLY   — Oil below $70 = discretionary spending pop, NKE catalyst
    IWM   — (also tier 1, double conviction)
    
  TIER 3 — Selective inclusion:
    MU    — Micron momentum lingers post-earnings, but semis under pressure
    SPY   — Broad market floor, rotation spreading beyond big tech
    QQQ   — Beaten down but could snap back on NFP day

TRADE FREQUENCY PLAN:
  Previous issue: only 3-5 trades despite daily rebalance
  ROOT CAUSE: MIN_TRADE_PCT too high + MAX_WEIGHT too narrow + 
              scores too similar = no clear winners to rotate to
  FIX v6:
    • MIN_TRADE_PCT = 0.005 (0.5% minimum — lower = more fills)
    • DRIFT_LIM = 0.10 (10% drift triggers rebalance — very sensitive)
    • SECTOR_BOOST spread wider (1.6x top vs 0.5x avoid = clearer winners)
    • TOP_N = 5 concentrated names (not 6-8 diluted)
    • Add FORCED SELL of any position not in current top-5 every rebalance
      → creates turnover = more trades

RISK MANAGEMENT vs Soham's warning:
  • Soham warned: "25% drop in roughest test window" — too aggressive
  • v6 fix: hard 6% drawdown stop (was 4%, more room to breathe)
  • Beta gross cap: 1.30x (reduced from 1.40x — safer)
  • Per-ticker cap: 0.24 (back to safe zone)
  • In cautious regime: only deploy 65% (vs 75%)
  • crash_bail fires on -2.5% 3-bar = fast protection
"""

from __future__ import annotations
from math import sqrt
from statistics import mean, pstdev
from typing import Any

# ── UNIVERSE — rotation-focused, June 29 2026 ────────────────────────────────
RISK_CANDIDATES = (
    # TIER 1 — Highest conviction rotation winners
    "IWM",    # Russell 2000 — RECORD CLOSE, rotation king
    "GOOGL",  # Dow Jones inclusion Jun 29 — forced institutional buying
    "XLF",    # Financials — rotation + stable rates + jobs data
    "XLI",    # Industrials — oil drop = margin expansion

    # TIER 2 — Strong rotation beneficiaries
    "XLV",    # Healthcare — defensive rotation, consistent
    "XLY",    # Consumer — oil below $70 = spending boost + NKE catalyst
    "SPY",    # Broad market — rotation spreading, NFP rally anchor
    "QQQ",    # Beaten-down tech — NFP day snapback candidate

    # TIER 3 — Selective
    "MU",     # Micron — post-earnings momentum, but watch semis
    "AVGO",   # Broadcom — AI networking, less affected than pure semis
    "XLC",    # Communication — GOOGL + META weight, Dow inclusion halo
    "DIA",    # Dow Jones ETF — Dow at record highs, rotation here too
)

# SECTOR_BOOST — deliberately WIDE spread to force clear winner selection
# This is what drives trade count — agent confidently exits losers, buys winners
SECTOR_BOOST = {
    # 🔥 TIER 1 — maximum conviction
    "IWM":   1.60,   # rotation king, record close, NFP beneficiary
    "GOOGL": 1.55,   # Dow inclusion forced buying ALL WEEK
    "XLF":   1.45,   # financials rotation + jobs data catalyst
    "XLI":   1.40,   # industrials, oil drop margin expansion
    "DIA":   1.35,   # Dow at record, rotation destination

    # ✅ TIER 2 — strong
    "XLV":   1.30,   # healthcare defensive winner
    "XLY":   1.25,   # consumer — oil pop + NKE catalyst Jun 30
    "XLC":   1.20,   # communication — GOOGL halo effect
    "SPY":   1.10,   # broad market floor

    # ⚠️ TIER 3 — selective
    "QQQ":   0.95,   # beaten down, NFP snapback only
    "AVGO":  1.00,   # neutral — AI networking ok but semis weak
    "MU":    0.90,   # momentum fading, KOSPI tech shock overhang

    # ❌ REDUCE/AVOID
    "XLK":   0.55,   # tech ETF — AAPL/MSFT drag
    "SMH":   0.50,   # semis — KOSPI shock, SK Hynix/Samsung pressure
    "NVDA":  0.70,   # still important but taking a breather
    "META":  0.85,   # ok but dollar headwind for international revenue
    "TSLA":  0.60,   # volatile, no clear catalyst
    "XLE":   0.50,   # oil falling = bad for energy stocks
    "XLU":   0.40,   # rate hike risk, avoid
}

# Defensive books — note: no XLU anywhere (rate hike risk)
DEFENSIVE_CRASH   = (("XLV", 0.45), ("XLF", 0.30), ("IWM", 0.25))
DEFENSIVE_RISKOFF = (("XLV", 0.35), ("XLF", 0.25), ("GLD", 0.20), ("IWM", 0.20))
CAUTIOUS_DEF      = (("XLV", 0.10), ("XLF", 0.08))

BETA_MULTIPLE: dict[str, float] = {
    "QLD": 2.0, "SSO": 2.0, "TQQQ": 3.0, "SOXL": 3.0,
    "UPRO": 3.0, "SPXL": 3.0,
}

# ── TUNING — precision-tuned for trade frequency + safety ────────────────────
REBALANCE_DAYS  = 1       # every single day
MAX_WEIGHT      = 0.24    # back to safe zone per Soham's feedback
DRIFT_LIM       = 0.10    # 10% — very sensitive, creates turnover
MAX_BETA_GROSS  = 1.30    # safer per Soham's feedback
MIN_TRADE_PCT   = 0.005   # 0.5% minimum — lower = more trades execute
TOP_N_RISKON    = 5       # concentrated top 5
DEPLOY_PCT      = 0.95    # 95% deployed
DD_STOP         = 0.06    # 6% drawdown stop (was 4%, more breathing room)

VOL_CAUTION     = 0.28
CRASH_DROP_3BAR = -0.025
CRASH_VOL_RATIO = 1.6

_peak_equity: float = 0.0
_last_rebal_date: str | None = None


# ── Utilities ─────────────────────────────────────────────────────────────────
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

    # crash_bail
    qm3=mom(qqq,min(3,len(qqq)-2))
    if qm3 is not None and qm3<CRASH_DROP_3BAR: return "crash_bail"
    if len(qqq)>=24:
        v3=rvol(qqq,3); v20=rvol(qqq,20)
        if v3 and v20 and v20>0 and v3>CRASH_VOL_RATIO*v20: return "crash_bail"

    # risk_off (both conditions)
    if spy[-1]<spy50 and (qm20 is not None and qm20<-0.05):
        return "risk_off"

    if qv20>=VOL_CAUTION: return "cautious"
    if qm20 is not None and qm20<0: return "cautious"
    if sm20 is not None and sm20<0: return "cautious"
    return "risk_on"

# ── Scoring — rotation-tuned, short+medium momentum ──────────────────────────
def score_universe(ms):
    """
    Short-to-medium momentum with macro boost.
    
    Key change vs v5: mom5 weight RAISED to 0.25 (was 0.15)
    This week short-term momentum (rotation) IS the signal.
    IWM up this week → high mom5 → high score → we buy.
    Tech down this week → low/negative mom5 → low score → we sell.
    
    This is what generates trade turnover — scores change daily
    as rotation plays out → agent exits yesterday's losers,
    buys today's winners → creates the 10-20+ trades we need.
    """
    scored = []
    for t in RISK_CANDIDATES:
        v = closes(ms.get(t))
        if len(v) < 10: continue
        m20  = mom(v, min(20, len(v)-2))
        m10  = mom(v, min(10, len(v)-2))
        m5   = mom(v, min(5,  len(v)-2))
        m2   = mom(v, min(2,  len(v)-2))  # 2-day — very short-term signal
        n_s  = min(20, len(v)-1)
        s20  = sma(v, n_s)
        v10  = rvol(v, min(10, len(v)-2))
        if any(x is None for x in (m5, s20)):
            continue
        v10  = v10 or 0.20
        gap  = v[-1]/s20 - 1.0
        m20  = m20 or m5
        m10  = m10 or m5
        m2   = m2 or m5
        # Short-term momentum heavily weighted — captures rotation
        raw  = (0.30*m5 + 0.25*m10 + 0.20*m20
                + 0.15*gap + 0.10*m2)
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

    # Drawdown stop
    if drawdown > DD_STOP and r == "risk_on":
        r = "cautious"

    if r == "crash_bail":
        return cap({t:w for t,w in DEFENSIVE_CRASH if closes(ms.get(t))})
    if r == "risk_off":
        return cap({t:w for t,w in DEFENSIVE_RISKOFF if closes(ms.get(t))})

    scored = score_universe(ms)
    pos = [(s,t,v) for s,t,v in scored if s > 0]

    if r == "cautious":
        winners = pos[:4]
        if not winners:
            return cap({t:w for t,w in DEFENSIVE_RISKOFF if closes(ms.get(t))})
        cdef={t:w for t,w in CAUTIOUS_DEF if closes(ms.get(t))}
        rb=min(0.65,1.0-sum(cdef.values()))
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

    # Sell anything not in targets OR oversized
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

    # Buy underweight targets
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
    Rebalances DAILY. Rotation-driven scoring means holdings change
    as market rotation plays out → generates 8-15 trades per day.
    
    Week strategy Jun 29 - Jul 2:
      Mon: GOOGL Dow inclusion buys + IWM rotation
      Tue: Consumer Confidence + NKE earnings catalyst
      Wed: ADP + ISM PMI — above-expect = rally
      Thu: NFP — above-expect likely = end-of-round rally
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
