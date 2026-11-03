# -*- coding: utf-8 -*-
"""Informe semanal de petróleo de la EIA (EE. UU.): existencias de crudo sin la reserva, gasolina, destilados y Cushing.
Fuente pública SIN clave: https://www.eia.gov/dnav/pet/hist_xls/<serie>w.xls (histórico completo en cada fichero).
Escribe DATOS_EIA/semanal.csv (fecha = viernes de cierre de la semana; se publica el miércoles siguiente, 16:30 de Madrid).
Lo usa el CORTO PETRÓLEO del bot de la cartera (nota de escasez: inventarios bajo su media de 5 años). Creado el 3-nov-2026."""
import os, io, urllib.request
import pandas as pd

SERIES = {'crudo': 'WCESTUS1', 'gasolina': 'WGTSTUS1', 'destilados': 'WDISTUS1', 'cushing': 'W_EPC0_SAX_YCUOK_MBBL'}
AQUI = os.path.dirname(os.path.abspath(__file__))


def serie(cod):
    req = urllib.request.Request(f'https://www.eia.gov/dnav/pet/hist_xls/{cod}w.xls', headers={'User-Agent': 'Mozilla/5.0'})
    x = pd.read_excel(io.BytesIO(urllib.request.urlopen(req, timeout=90).read()), sheet_name='Data 1', skiprows=2)
    return pd.Series(x.iloc[:, 1].astype(float).values, index=pd.to_datetime(x.iloc[:, 0])).dropna()


if __name__ == '__main__':
    df = pd.DataFrame({k: serie(v) for k, v in SERIES.items()}).sort_index()
    df.index.name = 'fecha'
    ruta = os.path.join(AQUI, 'semanal.csv')
    df.to_csv(ruta, float_format='%.0f')
    print(f'EIA: {len(df)} semanas, última {df.index[-1].date()} · crudo {df.crudo.iloc[-1]:,.0f} miles de barriles')
