# -*- coding: utf-8 -*-
"""Carga velas de esta carpeta con una sola línea.

    from cargar import velas
    df = velas('BTC', '1h')          # busca el activo en CRIPTO, TRADICIONAL o CRIPTO_PERPETUOS
    df = velas('oro', '1d')
    df = velas('BTC', '15m', perpetuo=True)

Temporalidades: 5m, 15m, 1h, 4h, 1d, 1w. Todas las horas en UTC. La última vela siempre está cerrada.
Necesita pandas y pyarrow (en Mac: python3 -m pip install pandas pyarrow).
"""
import os, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))

def velas(activo, tf, perpetuo=False):
    grupos = ['CRIPTO_PERPETUOS'] if perpetuo else ['CRIPTO', 'TRADICIONAL']
    for g in grupos:
        p = os.path.join(AQUI, g, activo, f'{tf}.parquet')
        if os.path.exists(p):
            return pd.read_parquet(p).set_index('fecha')
    raise FileNotFoundError(f'No hay {activo} en {tf}. Mira INDICE.csv para ver lo disponible.')

def financiacion(activo):
    return pd.read_parquet(os.path.join(AQUI, 'CRIPTO_PERPETUOS', activo, 'financiacion.parquet')).set_index('fecha')

if __name__ == '__main__':
    print(velas('BTC', '1d').tail())
