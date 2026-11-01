# -*- coding: utf-8 -*-
"""vol_btc.py · Volatilidad de 30 días de BTC y su percentil de 3 años (versión 1.0, 31-oct-2026).

Para qué (documento 06, punto 2, paso 5 quater; documento 11):
  1. SIN VENTA DEL TERCIO: si el percentil de AYER es <= 0,10, el REBOTE 4H de BTC, ETH, ADA, ZEC y LINK que entre HOY
     no vende 1/3 en +1 R (el stop pasa a la entrada igual). SOL no vende el tercio nunca (pirámide).
  2. AVISO DE COMPRESIÓN (contexto, sin estrellas ni tamaño): percentil <= 0,10 → «espera un movimiento más grande que el
     de las últimas semanas, sin dirección».
  3. RUPTURA TRAS COMPRESIÓN (contexto): cierre diario sobre el máximo de los 20 cierres anteriores con la volatilidad
     propia en su 20 % bajo algún día de los 10 anteriores.
Definiciones (backtests/2026-10-25-volatilidad-baja-y-sth.md y 2026-10-26-volatilidad-baja-variantes.md):
  v30 = desviación típica de las rentabilidades diarias (log) de 30 días, en %.
  pct3 = proporción de los últimos 1.095 días (incluido hoy, mínimo 730) con v30 <= la de hoy.
Uso:
  python3 vol_btc.py                         # velas de OKX (cierre diario UTC)
  python3 vol_btc.py --repo /home/claude/velas-backtest   # velas del repositorio + OKX para los últimos días
  python3 vol_btc.py --json vol_btc.json
Solo mide el pasado. No es asesoramiento."""
import sys, json, argparse, urllib.request
import numpy as np, pandas as pd

def okx_diario(inst='BTC-USDT', dias=1300):
    out, after = [], None
    while len(out) < dias:
        url = f'https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar=1Dutc&limit=100' + (f'&after={after}' if after else '')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        d = json.load(urllib.request.urlopen(req, timeout=30))['data']
        if not d: break
        out += d; after = d[-1][0]
    df = pd.DataFrame(out).iloc[:, [0, 4, 8]]; df.columns = ['t', 'close', 'confirm']
    df = df[df.confirm == '1']                       # solo velas cerradas
    df.index = pd.to_datetime(df.t.astype('int64'), unit='ms'); return df.close.astype(float).sort_index()

def repo_diario(repo, activo='BTC'):
    sys.path.insert(0, repo)
    from cargar import velas
    s = velas(activo, '1d').cierre.astype(float); s.index = pd.to_datetime(s.index).normalize()
    return s[~s.index.duplicated(keep='last')]

def calcular(c):
    c = c.asfreq('D').ffill()
    v = np.log(c).diff().rolling(30).std() * 100
    pct = v.rolling(1095, min_periods=730).apply(lambda x: (x <= x[-1]).mean(), raw=True)
    comp = (pct <= 0.20).rolling(10).max().astype(bool)
    rup = (c > c.rolling(20).max().shift(1)) & comp
    return c, v, pct, rup

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo'); ap.add_argument('--json')
    a = ap.parse_args()
    if a.repo:
        s = repo_diario(a.repo)
        try:
            o = okx_diario(dias=120); s = pd.concat([s, o[o.index > s.index[-1]]])
        except Exception as e:
            print('aviso: sin OKX', e, file=sys.stderr)
    else:
        s = okx_diario()
    c, v, pct, rup = calcular(s)
    hoy = c.index[-1]
    r = dict(fecha_cierre=str(hoy.date()), precio=round(float(c.iloc[-1]), 2), v30_pct=round(float(v.iloc[-1]), 3),
             percentil_3a=round(float(pct.iloc[-1]), 4),
             sin_venta_tercio=bool(pct.iloc[-1] <= 0.10),      # vale para las entradas del día SIGUIENTE a este cierre
             aviso_compresion=bool(pct.iloc[-1] <= 0.10),
             ruptura_tras_compresion=bool(rup.iloc[-1]),
             texto=None)
    if r['sin_venta_tercio']:
        r['texto'] = (f"Volatilidad de BTC en su {r['percentil_3a']*100:.0f} % más bajo de 3 años ({r['v30_pct']:.2f} % diario): "
                      "sin venta del tercio en el REBOTE 4H de BTC, ETH, ADA, ZEC y LINK que entre hoy. Espera un movimiento "
                      "más grande que el de las últimas semanas, sin dirección (13 episodios desde 2013: volatilidad × 1,6 a 60 días).")
    else:
        r['texto'] = f"Volatilidad de BTC en su {r['percentil_3a']*100:.0f} % de 3 años ({r['v30_pct']:.2f} % diario): venta del tercio normal."
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.json: json.dump(r, open(a.json, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
