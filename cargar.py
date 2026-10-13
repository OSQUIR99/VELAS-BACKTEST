# -*- coding: utf-8 -*-
"""Carga velas de esta carpeta con una sola línea.

    from cargar import velas, financiacion
    df = velas('BTC', '1h')                   # contado
    df = velas('BTC', '15m', perpetuo=True)   # perpetuo de Binance
    df = velas('oro', '1d')
    df = velas('shy', '1d', ajustado=True)    # fondos cotizados: precio con dividendos reinvertidos
    df = velas('dominancia_btc', '4h')
    df = velas('AVAX', '1h')                  # también busca en ALTCOINS_SECUNDARIAS
    f  = financiacion('SOL')

Dónde busca, por este orden:
    CARPETA_DE_BACKTEST/CRIPTO, TRADICIONAL, INDICES_CRIPTO
    ALTCOINS_SECUNDARIAS/CONTADO
    (perpetuo=True) CARPETA_DE_BACKTEST/CRIPTO_PERPETUOS y ALTCOINS_SECUNDARIAS/PERPETUOS

Temporalidades: 5m, 15m, 1h, 4h, 1d, 1w. Todas las horas en UTC. La última vela siempre está cerrada.
Necesita pandas y pyarrow (en Mac: python3 -m pip install pandas pyarrow).
"""
import os
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
CONTADO = ['CARPETA_DE_BACKTEST/CRIPTO', 'CARPETA_DE_BACKTEST/TRADICIONAL',
           'CARPETA_DE_BACKTEST/INDICES_CRIPTO', 'ALTCOINS_SECUNDARIAS/CONTADO']
PERPETUOS = ['CARPETA_DE_BACKTEST/CRIPTO_PERPETUOS', 'ALTCOINS_SECUNDARIAS/PERPETUOS']


def _buscar(activo, nombre, grupos):
    for g in grupos:
        p = os.path.join(AQUI, g, activo, nombre)
        if os.path.exists(p):
            return p
    return None


def velas(activo, tf, perpetuo=False, ajustado=False):
    nombre = f'{tf}_ajustado_dividendos.parquet' if ajustado else f'{tf}.parquet'
    p = _buscar(activo, nombre, PERPETUOS if perpetuo else CONTADO)
    if p is None:
        raise FileNotFoundError(f'No hay {activo} en {tf}{" ajustado" if ajustado else ""}. Mira INDICE.csv para ver lo disponible.')
    return pd.read_parquet(p).set_index('fecha')


def financiacion(activo):
    p = _buscar(activo, 'financiacion.parquet', PERPETUOS)
    if p is None:
        raise FileNotFoundError(f'No hay financiación de {activo}.')
    return pd.read_parquet(p).set_index('fecha')


if __name__ == '__main__':
    print(velas('BTC', '1d').tail())
