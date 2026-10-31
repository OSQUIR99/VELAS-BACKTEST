# -*- coding: utf-8 -*-
"""Reconstrucción de los cortos en vigor (documento 25, 27/28-oct-2026) a partir de su definición escrita.
Solo backtest; solo mide el pasado.

  CORTO SECTOR: 12 fondos de sectores (XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH).
     Tendencia bajista: el sector Y el S&P 500 cierran bajo su media de 200, y las dos medias están más bajas que hace 20 sesiones.
     Disparo: RSI(2) del sector > 90 al cierre. Entrada: apertura siguiente. Stop 2,5 ATR(14 Wilder) fijo.
     Salida: primer cierre bajo la media de 5 (se sale en la apertura siguiente) o como mucho 10 sesiones.
     Tamaño 0,5 R; 0,25 R si el dólar (DXY, cierre del día anterior) no ha subido en 63 sesiones. Fuera del freno de racha.
     El corto paga el dividendo del fondo.
  CORTO ÍNDICES CRÉDITO: S&P 500, Nasdaq 100, Dow y Russell 2000 (futuros).
     Tendencia: el índice cierra bajo su media de 200 Y HYG cierra bajo su media de 50. Disparo RSI(2) > 90.
     Entrada, stop y salida iguales. Tamaño 0,5 R. Fuera del freno de racha.
Una posición a la vez por activo. Coste 0,02 % ida y vuelta.
Salida: listas en formato del motor (<familia>.parquet y <familia>_diario.parquet).
"""
import sys, os
sys.path.insert(0, '/home/claude/velas-backtest')
import numpy as np
import pandas as pd
from cargar import velas

COSTE = 0.0002
SECTORES = {'XLK': 'sector_tecnologia', 'XLF': 'sector_financieras', 'XLE': 'sector_energia', 'XLV': 'sector_salud',
            'XLI': 'sector_industria', 'XLY': 'sector_consumo_ciclico', 'XLP': 'sector_consumo_basico',
            'XLU': 'sector_servicios_publicos', 'XLB': 'sector_materiales', 'XLRE': 'sector_inmobiliario',
            'XLC': 'sector_comunicaciones', 'SMH': 'semiconductores'}
INDICES = {'SPX': 'sp500', 'NDX': 'nasdaq100', 'DJI': 'dowjones', 'RUT': 'russell2000'}


def diario(nombre, ajustado=False):
    d = velas(nombre, '1d', ajustado=ajustado).copy()
    d.index = (pd.to_datetime(d.index) + pd.Timedelta(hours=6)).normalize()   # fecha de la sesión (velas de la tarde anterior)
    d = d[~d.index.duplicated(keep='last')]
    return d[['apertura', 'maximo', 'minimo', 'cierre']].astype(float)


def rsi_wilder(c, n=2):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def atr_wilder(d, n=14):
    pc = d.cierre.shift(1)
    tr = pd.concat([d.maximo - d.minimo, (d.maximo - pc).abs(), (d.minimo - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def dividendos(nombre, idx):
    """Dividendo por acción en su fecha ex, a partir de la serie ajustada y la normal."""
    try:
        a = velas(nombre, '1d', ajustado=True).cierre.astype(float)
    except Exception:
        return pd.Series(0.0, index=idx)
    a.index = (pd.to_datetime(a.index) + pd.Timedelta(hours=6)).normalize(); a = a[~a.index.duplicated(keep='last')]
    c = diario(nombre).cierre
    r = (a / c).reindex(idx).ffill()
    f = (r.shift(1) / r)  # = 1 - D / c_{ex-1} el día ex
    D = (c.shift(1).reindex(idx) * (1 - f)).where((1 - f) > 1e-6, 0.0).fillna(0.0)
    return D


def simular_corto(d, permiso, tam, activo, familia, bloque, div=None, desde='1999-01-01'):
    """d: OHLC diario; permiso: booleana al cierre (tendencia bajista + disparo); tam: tamaño en R al cierre de la señal."""
    d = d[d.index >= pd.Timestamp(desde) - pd.Timedelta(days=400)]
    atr = atr_wilder(d); m5 = d.cierre.rolling(5).mean()
    sig = permiso.reindex(d.index).fillna(False).astype(bool) & (d.index >= pd.Timestamp(desde))
    o, h, l, c = d.apertura.values, d.maximo.values, d.minimo.values, d.cierre.values
    idx = d.index
    div = div.reindex(idx).fillna(0.0).values if div is not None else np.zeros(len(idx))
    ops, dia = [], []
    i = 0
    n = len(idx)
    while i < n - 1:
        if not sig.iloc[i] or not np.isfinite(atr.iloc[i]) or tam.get(idx[i], np.nan) != tam.get(idx[i], np.nan):
            i += 1; continue
        ts = float(tam.get(idx[i]))
        e_i = i + 1                      # entrada en la apertura siguiente
        E = o[e_i]; riesgo = 2.5 * float(atr.iloc[i]); SL = E + riesgo
        X = None; motivo = None; k = e_i; divs = 0.0; mae = 0.0; mfe = 0.0
        lat = []
        while k < n:
            divs += div[k] if k > e_i else 0.0            # el corto paga el dividendo si estaba abierto al cierre anterior
            if k > e_i and o[k] >= SL and X is None:      # salto por encima del stop en la apertura
                X = o[k]; motivo = 'stop (hueco)'; break
            if h[k] >= SL:
                X = SL if k > e_i or o[k] < SL else o[k]; motivo = 'stop'; break
            mae = min(mae, (E - h[k] - divs) / riesgo); mfe = max(mfe, (E - l[k] - divs) / riesgo)
            lat.append((idx[k], (E - c[k] - divs) / riesgo))
            sesiones = k - e_i + 1
            if c[k] < m5.iloc[k] or sesiones >= 10:
                if k + 1 < n:
                    X = o[k + 1]; divs += div[k + 1]; k = k + 1
                    motivo = 'media 5' if c[k - 1] < m5.iloc[k - 1] else '10 sesiones'
                else:
                    X = None
                break
            k += 1
        if X is None:      # sigue abierta al final de los datos: se valora al último cierre
            k = n - 1; X = c[k]; motivo = 'abierta'
        rb = (E - X - divs) / riesgo - COSTE * E / riesgo
        oid = f'{familia}-{activo}-{idx[i].strftime("%Y%m%d")}'
        t_sal = idx[k] + pd.Timedelta(hours=13, minutes=30) if motivo in ('media 5', '10 sesiones', 'stop (hueco)') else idx[k] + pd.Timedelta(hours=17)
        ops.append(dict(id=oid, familia=familia, activo=activo, direccion=-1,
                        t_senal=idx[i] + pd.Timedelta(hours=20), t_entrada=idx[e_i] + pd.Timedelta(hours=13, minutes=30),
                        t_salida=t_sal, entrada=E, sl_inicial=SL, salida=X, r_bruto=rb, tam_R=ts, r_final=rb * ts,
                        estrellas=np.nan, mae_R=mae, mfe_R=mfe, motivo_salida=motivo, bloque=bloque))
        for f, v in lat:
            if f < idx[k]:
                dia.append(dict(id=oid, fecha=f, r_latente=v * ts))
        dia.append(dict(id=oid, fecha=idx[k], r_latente=rb * ts))
        i = k if k > i else i + 1        # una posición a la vez por activo
    return pd.DataFrame(ops), pd.DataFrame(dia)


def construir(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    spx = diario('sp500'); s200 = spx.cierre.rolling(200).mean()
    spx_baj = (spx.cierre < s200) & (s200 < s200.shift(20))
    dxy = diario('dolar_dxy').cierre
    dxy_sube = (dxy > dxy.shift(63)).shift(1)       # con el cierre del día anterior
    # ---- CORTO SECTOR
    O, Dd = [], []
    for act, nom in SECTORES.items():
        d = diario(nom)
        m200 = d.cierre.rolling(200).mean()
        baj = (d.cierre < m200) & (m200 < m200.shift(20)) & spx_baj.reindex(d.index).fillna(False)
        disp = rsi_wilder(d.cierre) > 90
        tam = pd.Series(np.where(dxy_sube.reindex(d.index).ffill().fillna(False).astype(bool), 0.5, 0.25), index=d.index)
        o, dd = simular_corto(d, baj & disp, tam, act, 'corto_sector', 'bolsa_eeuu', dividendos(nom, d.index), '2000-01-01')
        O.append(o); Dd.append(dd)
    O = pd.concat(O, ignore_index=True); Dd = pd.concat(Dd, ignore_index=True)
    O.to_parquet(f'{carpeta}/corto_sector.parquet'); Dd.to_parquet(f'{carpeta}/corto_sector_diario.parquet')
    # ---- CORTO ÍNDICES CRÉDITO
    hyg = diario('hyg').cierre; hyg_flojo = hyg < hyg.rolling(50).mean()
    O2, D2 = [], []
    for act, nom in INDICES.items():
        d = diario(nom)
        m200 = d.cierre.rolling(200).mean()
        baj = (d.cierre < m200) & hyg_flojo.reindex(d.index).fillna(False)
        disp = rsi_wilder(d.cierre) > 90
        tam = pd.Series(0.5, index=d.index)
        o, dd = simular_corto(d, baj & disp, tam, act, 'corto_indices_credito', 'bolsa_eeuu', None, '2007-06-01')
        O2.append(o); D2.append(dd)
    O2 = pd.concat(O2, ignore_index=True); D2 = pd.concat(D2, ignore_index=True)
    O2.to_parquet(f'{carpeta}/corto_indices_credito.parquet'); D2.to_parquet(f'{carpeta}/corto_indices_credito_diario.parquet')
    return O, O2


if __name__ == '__main__':
    car = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/caidas/listas_cortos'
    A, B = construir(car)
    for nom, X in (('CORTO SECTOR', A), ('CORTO ÍNDICES CRÉDITO', B)):
        r = X.r_bruto
        print(nom, 'operaciones', len(X), 'desde', X.t_entrada.min().date(), '| R final total', round(X.r_final.sum(), 1),
              '| R por operación (por unidad)', round(r.mean(), 3), '| acierto', round((r > 0).mean() * 100), '%')
        X['ano'] = X.t_entrada.dt.year
        print('   por año (R final):', X.groupby('ano').r_final.sum().round(1).to_dict())
        print('   motivos:', X.motivo_salida.value_counts().to_dict())
