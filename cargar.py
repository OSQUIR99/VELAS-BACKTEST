# -*- coding: utf-8 -*-
"""Carga velas de esta carpeta con una sola línea.

    from cargar import velas, financiacion
    df = velas('BTC', '1h')                   # contado
    df = velas('BTC', '15m', perpetuo=True)   # perpetuo de Binance
    df = velas('oro', '1d')
    df = velas('shy', '1d', ajustado=True)    # fondos cotizados: precio con dividendos reinvertidos
    df = velas('dominancia_btc', '4h')
    df = velas('AVAX', '1h')                  # también busca en ALTCOINS_SECUNDARIAS
    df = velas('HST', '1d')                   # acciones de la lista de seguimiento (símbolo de Yahoo: RACE.MI, RAND.AS...)
    f  = financiacion('SOL')

Dónde busca, por este orden:
    CARPETA_DE_BACKTEST/CRIPTO, TRADICIONAL, INDICES_CRIPTO
    ALTCOINS_SECUNDARIAS/CONTADO, CARPETA_DE_BACKTEST/ACCIONES (solo 1d)
    (perpetuo=True) CARPETA_DE_BACKTEST/CRIPTO_PERPETUOS y ALTCOINS_SECUNDARIAS/PERPETUOS

Temporalidades: 5m, 15m, 1h, 4h, 1d, 1w. Desde el 18-oct-2026 se actualizan solas cada día (ACTUALIZACION/);
    velas(..., actualizado=False) da la copia fija original. Todas las horas en UTC. La última vela siempre está cerrada.
Necesita pandas y pyarrow (en Mac: python3 -m pip install pandas pyarrow).
"""
import os
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
CONTADO = ['CARPETA_DE_BACKTEST/CRIPTO', 'CARPETA_DE_BACKTEST/TRADICIONAL',
           'CARPETA_DE_BACKTEST/INDICES_CRIPTO', 'ALTCOINS_SECUNDARIAS/CONTADO',
           'CARPETA_DE_BACKTEST/ACCIONES']
PERPETUOS = ['CARPETA_DE_BACKTEST/CRIPTO_PERPETUOS', 'ALTCOINS_SECUNDARIAS/PERPETUOS']


def _buscar(activo, nombre, grupos):
    for g in grupos:
        p = os.path.join(AQUI, g, activo, nombre)
        if os.path.exists(p):
            return p
    return None


def _con_nuevas(p, df):
    """Añade las velas cerradas que GitHub guarda cada día en ACTUALIZACION/velas (ver ACTUALIZACION/LEEME.md)."""
    rel = os.path.relpath(os.path.dirname(p), AQUI)
    d = os.path.join(AQUI, 'ACTUALIZACION', 'velas', rel)
    if not os.path.isdir(d):
        return df
    tf = os.path.basename(p)[:-len('.parquet')]
    partes = []
    for raiz, _, archivos in os.walk(d):
        for a in archivos:
            if a.endswith('.parquet'):
                x = pd.read_parquet(os.path.join(raiz, a))
                partes.append(x[x.tf == tf])
    if not partes:
        return df
    n = pd.concat(partes)
    n = n[n.fecha > df.fecha.max()][[c for c in df.columns if c in n.columns]]
    if not len(n):
        return df
    return pd.concat([df, n]).drop_duplicates('fecha', keep='last').sort_values('fecha').reset_index(drop=True)


def velas(activo, tf, perpetuo=False, ajustado=False, actualizado=True):
    """actualizado=False: la copia fija original (para repetir un backtest con los mismos datos)."""
    nombre = f'{tf}_ajustado_dividendos.parquet' if ajustado else f'{tf}.parquet'
    p = _buscar(activo, nombre, PERPETUOS if perpetuo else CONTADO)
    if p is None:
        raise FileNotFoundError(f'No hay {activo} en {tf}{" ajustado" if ajustado else ""}. Mira INDICE.csv para ver lo disponible.')
    df = pd.read_parquet(p)
    if actualizado:
        df = _con_nuevas(p, df)
    return df.set_index('fecha')


def financiacion(activo, actualizado=True):
    p = _buscar(activo, 'financiacion.parquet', PERPETUOS)
    if p is None:
        raise FileNotFoundError(f'No hay financiación de {activo}.')
    df = pd.read_parquet(p)
    if actualizado:
        df = _con_nuevas(p, df)
    return df.set_index('fecha')


if __name__ == '__main__':
    print(velas('BTC', '1d').tail())
