# -*- coding: utf-8 -*-
"""Precios diarios y correlaciones para el motor de cartera (solo datos pasados).

- cierre_diario(activo): busca en velas-backtest (con alias), en las cachés de Yahoo de sesiones anteriores
  y, si no está, lo baja de Yahoo. Guarda todo en /home/claude/motor/cache/.
- Correlaciones: rendimientos logarítmicos en días hábiles (la cripto del fin de semana se suma al lunes).
  ρ(a, b, fecha) = la mayor de la de 60 sesiones y la de 1 año (252), con datos HASTA EL DÍA ANTERIOR.
"""
import os, sys, json, glob, subprocess, time
import numpy as np
import pandas as pd

sys.path.insert(0, '/home/claude/velas-backtest')
from cargar import velas

CACHE = '/home/claude/motor/cache'
os.makedirs(CACHE, exist_ok=True)
YAHOO_DIRS = ['/tmp/claude-0/-home-claude/7325dc31-de4b-59dd-a91f-709f76879a05/scratchpad/atr/yahoo',
              '/home/claude/bt_stop/datos_yahoo']

ALIAS = {
    'SPY': 'sp500', 'SP500': 'sp500', 'S&P500': 'sp500', 'ES': 'sp500', 'ESZ6': 'sp500', 'SPX': 'sp500',
    'QQQ': 'nasdaq100', 'NDX': 'nasdaq100', 'NQ': 'nasdaq100', 'NQZ6': 'nasdaq100', 'NASDAQ100': 'nasdaq100',
    'DIA': 'dowjones', 'YM': 'dowjones', 'DOW': 'dowjones', 'IWM': 'russell2000', 'RTY': 'russell2000',
    'RUSSELL': 'russell2000', 'DAX': 'dax', 'SMH': 'semiconductores', 'IGV': 'software',
    'XLK': 'sector_tecnologia', 'XLC': 'sector_comunicaciones', 'XLY': 'sector_consumo_ciclico',
    'XLP': 'sector_consumo_basico', 'XLE': 'sector_energia', 'XLF': 'sector_financieras', 'XLI': 'sector_industria',
    'XLV': 'sector_salud', 'XLU': 'sector_servicios_publicos', 'XLB': 'sector_materiales', 'XLRE': 'sector_inmobiliario',
    'ORO': 'oro', 'GOLD': 'oro', 'GC': 'oro', 'XAU': 'oro', 'XAUUSD': 'oro', 'PLATA': 'plata', 'SILVER': 'plata',
    'SI': 'plata', 'XAG': 'plata', 'BRENT': 'petroleo_brent', 'BZ': 'petroleo_brent', 'BRN': 'petroleo_brent',
    'WTI': 'petroleo_wti', 'CL': 'petroleo_wti', 'PETROLEO': 'petroleo_wti', 'COBRE': 'cobre', 'HG': 'cobre',
    'GAS': 'gas_natural', 'NG': 'gas_natural', 'GAS_NATURAL': 'gas_natural', 'MAIZ': 'maiz', 'ZC': 'maiz',
    'TRIGO': 'trigo', 'ZW': 'trigo', 'PLATINO': 'platino', 'PL': 'platino', 'PALADIO': 'paladio', 'PA': 'paladio',
    'GASOLINA': 'gasolina', 'RB': 'gasolina', 'GASOLEO': 'gasoleo', 'HO': 'gasoleo',
    'DJI': 'dowjones', 'DJIA': 'dowjones', 'RUT': 'russell2000', 'NDX100': 'nasdaq100', 'US500': 'sp500',
    'SHY': 'shy', 'TLT': 'tlt', 'IEF': 'ief', 'HYG': 'hyg', 'UUP': 'uup',
}


def _norm(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize() if getattr(df.index, 'tz', None) is not None \
        else pd.to_datetime(df.index).normalize()
    df = df[~df.index.duplicated(keep='last')]
    return df


def _de_velas(nombre):
    for cand in (nombre, nombre.lower(), ALIAS.get(nombre.upper()), ALIAS.get(nombre.upper(), '').lower() or None,
                 nombre.upper()):
        if not cand:
            continue
        try:
            d = velas(cand, '1d')
            return _norm(d).cierre.astype(float)
        except Exception:
            pass
    return None


def _de_yahoo_json(ruta):
    r = json.load(open(ruta))['chart']['result'][0]
    q = r['indicators']['quote'][0]
    s = pd.Series(q['close'], index=pd.to_datetime(r['timestamp'], unit='s').normalize()).dropna()
    return s[~s.index.duplicated(keep='last')].astype(float)


def _de_cache_yahoo(nombre):
    for d in YAHOO_DIRS:
        for patron in (f'{nombre}.json', f'{nombre}_1d.json'):
            p = os.path.join(d, patron)
            if os.path.exists(p):
                try:
                    return _de_yahoo_json(p)
                except Exception:
                    pass
    return None


def _bajar_yahoo(sym):
    p = os.path.join(CACHE, f'yahoo_{sym}.json')
    if not os.path.exists(p):
        for k in range(3):
            r = subprocess.run(['curl', '-s', '-A', 'Mozilla/5.0',
                                f'https://query{1 + k % 2}.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&period1=946684800&period2=1792500000'],
                               capture_output=True, text=True, timeout=60)
            try:
                d = json.loads(r.stdout)
                if d['chart']['result'][0].get('timestamp'):
                    open(p, 'w').write(r.stdout)
                    break
            except Exception:
                time.sleep(2)
    if os.path.exists(p):
        try:
            return _de_yahoo_json(p)
        except Exception:
            return None
    return None


YAHOO_ALIAS = {'HO': 'HO=F', 'RB': 'RB=F', 'GASOLINA': 'RB=F', 'GASOLEO': 'HO=F', 'BRENT': 'BZ=F', 'WTI': 'CL=F'}


def activo_base(activo):
    """'SHY (tercio 200)' -> 'SHY'; 'BTC-USDT' / 'BTCUSDT' -> 'BTC'."""
    a = str(activo).split(' (')[0].strip()
    for suf in ('-USDT', 'USDT', '-USD', '/USDT'):
        if a.upper().endswith(suf) and len(a) > len(suf):
            a = a[:-len(suf)]
    return a


def cierre_diario(activo):
    activo = activo_base(activo)
    p = os.path.join(CACHE, f'cierre_{activo.replace("/", "_")}.parquet')
    if os.path.exists(p):
        return pd.read_parquet(p).iloc[:, 0]
    s = _de_velas(activo)
    fuente = 'velas'
    if s is None:
        s = _de_cache_yahoo(activo)
        fuente = 'yahoo-cache'
    if s is None:
        s = _bajar_yahoo(YAHOO_ALIAS.get(activo.upper(), activo))
        fuente = 'yahoo'
    if s is None or len(s) < 30:
        return None
    s = s[s > 0]
    s.name = activo
    s.to_frame().to_parquet(p)
    return s


class Correlaciones:
    def __init__(self, activos, ventana_corta=60, ventana_larga=252, defecto=None):
        self.activos = list(dict.fromkeys(activos))
        series = {}
        self.sin_datos = []
        self.base = {a: activo_base(a) for a in self.activos}
        for a in self.activos:
            s = cierre_diario(a)
            if s is None:
                self.sin_datos.append(a)
            else:
                series[a] = s
        bd = pd.bdate_range('1985-01-01', pd.Timestamp.today().normalize())
        cols = {}
        for a, s in series.items():
            s = s.sort_index()
            # cierre en día hábil: el último cierre conocido hasta ese día (la cripto del finde va al lunes)
            x = s.reindex(s.index.union(bd)).ffill(limit=4).reindex(bd)
            primera = s.index.min()
            x[x.index < primera] = np.nan
            cols[a] = np.log(x).diff()
        self.R = pd.DataFrame(cols, index=bd)
        self.fechas = self.R.index.values
        self.M = self.R.values
        self.col = {a: i for i, a in enumerate(self.R.columns)}
        self.vc, self.vl = ventana_corta, ventana_larga
        self.cache = {}
        self.defecto = defecto or (lambda a, b: 0.3)

    def t_de(self, fecha):
        """Posición en días hábiles: los rendimientos usados son los ANTERIORES a esa fecha."""
        return int(np.searchsorted(self.fechas, np.datetime64(pd.Timestamp(fecha).normalize()), side='left'))

    def _serie_par(self, a, b):
        k = (a, b) if a < b else (b, a)
        v = self.cache.get(k)
        if v is not None:
            return v
        ia, ib = self.col.get(a), self.col.get(b)
        if ia is None or ib is None:
            v = None
        else:
            x = self.R.iloc[:, ia].copy()
            y = self.R.iloc[:, ib].copy()
            ambos0 = (x == 0) & (y == 0)
            x[ambos0] = np.nan
            y[ambos0] = np.nan
            c1 = x.rolling(self.vc, min_periods=40).corr(y).values
            c2 = x.rolling(self.vl, min_periods=120).corr(y).values
            v = np.fmax(c1, c2)
        self.cache[k] = v
        return v

    def rho_t(self, a, b, t):
        if a == b or self.base.get(a, a) == self.base.get(b, b):
            return 1.0
        v = self._serie_par(a, b)
        if v is None or t <= 0:
            return self.defecto(a, b)
        x = v[t - 1]
        if x != x:
            return self.defecto(a, b)
        return float(x)

    def rho(self, a, b, fecha):
        """Correlación prudente (la mayor de 60 sesiones y 252) con datos hasta el día anterior a `fecha`."""
        return self.rho_t(a, b, self.t_de(fecha))
