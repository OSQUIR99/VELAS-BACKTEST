# -*- coding: utf-8 -*-
"""E1 (REBOTE ÍNDICE) con el generador ORIGINAL de la lista del motor (drive-pendiente/bolsa-gestion/listas_bolsa.py,
20-oct-2026), cambiando SOLO la salida de los índices S&P, Nasdaq 100 y Dow. Entradas, stop 2,5 ATR, regla de posiciones
(una por activo; la segunda solo con un disparador más bajo; máximo 2), tamaño por puntos y tope de 3 R al día: sin tocar.
Sectores y Russell (solo contexto en la cartera, pero entran en el conteo de puntos y en el tope diario del generador)
siguen con su salida de siempre.

Salidas (todas al cierre; el stop y los huecos, como el motor original):
  base    : 1.er cierre > media de 5 (máx. 10 sesiones desde la señal)            = lista del motor
  seguir5 : tras el 1.er cierre > media 5, seguir mientras cierre > media 5; salir al 1.er cierre < media 5 (máx. 20)
  rsi90   : 1.er cierre con RSI(2) > 90 (máx. 10)
  minant  : tras el 1.er cierre > media 5, salir al 1.er cierre < mínimo del día anterior (máx. 20)
  alternativas (paso 5 del documento 23, fijadas tras ver las tres primeras en la cartera):
  seguir5_max10 : seguir5 con el máximo de 10 sesiones de la base
  mitad         : mitad al 1.er cierre > media 5 (la base) y la otra mitad con seguir5 (máx. 20)
Uso: python3 gen_e1.py <carpeta_salida>  → bolsa_e1_<salida>.parquet (+ _diario) por salida, en el formato del motor.
"""
import sys, os, inspect, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/drive-pendiente/bolsa-gestion')
import numpy as np, pandas as pd
import e1_motor as M
import e1_pruebas as P
import listas_bolsa as LB

IDX = ('SPX', 'NDX', 'DJI')
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'

# --- parche de la salida: copia del simular original con tres modos nuevos (el resto, idéntico)
src = inspect.getsource(M.simular)
a1 = "    camino = []\n    mae, mfe = 0.0, 0.0\n"
assert a1 in src
src = src.replace(a1, a1 + "    armado = False\n    rsi = A['rsi2']\n")
a2 = "        if cfg.get('max_total') and j - i >= cfg['max_total']:"
assert a2 in src
nuevo = """        if modo == 'rsi90':
            if rsi[j] > 90 or j - i >= max_ses:
                return fin(j, c[j], 'rapida' if rsi[j] > 90 else 'tiempo')
        if modo in ('seguir5', 'minant', 'mitad'):
            if not armado:
                if c[j] > sma[j]:
                    armado = True
                    if modo == 'mitad':                   # vende la mitad al cierre de la señal base (con su coste)
                        vendido = 0.5
                        cobro += 0.5 * (c[j] - e) / U - 0.5 * slip * c[j] / U
            elif (modo in ('seguir5', 'mitad') and c[j] < sma[j]) or (modo == 'minant' and c[j] < l[j - 1]):
                return fin(j, c[j], 'rapida')
            if j - i >= max_ses:
                return fin(j, c[j], 'tiempo')
"""
src = src.replace(a2, nuevo + a2)
ns = dict(M.__dict__)
exec(compile(src, M.__file__ + ' (parche salida)', 'exec'), ns)
M.simular = ns['simular']          # correr() lo busca en el módulo

SALIDAS = {'base': {}, 'seguir5': {'salida': 'seguir5', 'max_ses': 20},
           'rsi90': {'salida': 'rsi90', 'max_ses': 10}, 'minant': {'salida': 'minant', 'max_ses': 20},
           # alternativas del paso 5 del documento 23 (fijadas DESPUÉS de ver que las tres primeras suben la caída)
           'seguir5_max10': {'salida': 'seguir5', 'max_ses': 10}, 'mitad': {'salida': 'mitad', 'max_ses': 20}}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    D = P.cargar_todo()
    for nom, ex in SALIDAS.items():
        T = LB.familia(D, {k: ex for k in IDX} if ex else None)
        LB.puntos_y_tope(D, T)
        L, Dd = LB.a_lista(T, D, 'bolsa_e1')
        L.to_parquet(f'{OUT}/bolsa_e1_{nom}.parquet', index=False)
        Dd.to_parquet(f'{OUT}/bolsa_e1_{nom}_diario.parquet', index=False)
        I = L[L.activo.isin(IDX)]
        ses = np.array([np.busday_count(a.date(), b.date()) for a, b in zip(I.t_entrada, I.t_salida)])
        print(f'{nom:8s} índices {len(I)} ops · R {I.r_final.sum():.1f} · R/op (×tam) {I.r_final.mean():.3f} · '
              f'R bruto/op {I.r_bruto.mean():.3f} · sesiones medias {ses.mean():.1f} · motivos {I.motivo_salida.value_counts().to_dict()}',
              flush=True)
