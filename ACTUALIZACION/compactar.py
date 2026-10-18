# -*- coding: utf-8 -*-
"""Junta los archivos diarios de ACTUALIZACION/velas en uno por activo y semestre (cada 6 meses: 2 de enero y 2 de julio).

  python3 ACTUALIZACION/compactar.py

Solo junta semestres ya terminados: ACTUALIZACION/velas/<carpeta>/<activo>/<AAAA>-S1.parquet (enero-junio) o -S2 (julio-diciembre),
y borra los diarios de ese semestre. cargar.py y actualizar.py leen igual los dos formatos, así que no cambia nada al usarlo:
solo hace que cargar velas sea más rápido (menos archivos que abrir).
"""
import os, re, datetime as dt
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(AQUI, 'velas')
HOY = dt.date.today()
INICIO_SEMESTRE = dt.date(HOY.year, 1 if HOY.month <= 6 else 7, 1)
DIA = re.compile(r'(\d{4})-(\d{2})-(\d{2})\.parquet$')

juntados = borrados = 0
for raiz, carpetas, archivos in os.walk(DIR):
    grupos = {}
    for a in archivos:
        m = DIA.match(a)
        if not m: continue
        d = dt.date(int(m[1]), int(m[2]), int(m[3]))
        if d >= INICIO_SEMESTRE: continue                     # el semestre en curso se queda en diarios
        grupos.setdefault(f"{d.year}-S{1 if d.month <= 6 else 2}", []).append(os.path.join(raiz, a))
    if not grupos: continue
    activo = os.path.dirname(raiz)                            # .../<activo>/<AAAA-MM>/<día>.parquet
    for sem, rutas in grupos.items():
        destino = os.path.join(activo, f'{sem}.parquet')
        partes = [pd.read_parquet(p) for p in rutas] + ([pd.read_parquet(destino)] if os.path.exists(destino) else [])
        df = pd.concat(partes).drop_duplicates(['tf', 'fecha'], keep='last').sort_values(['tf', 'fecha']).reset_index(drop=True)
        df.to_parquet(destino, index=False, compression='zstd')
        for p in rutas: os.remove(p)
        juntados += 1; borrados += len(rutas)
for raiz, carpetas, archivos in sorted(os.walk(DIR), reverse=True):   # quita las carpetas de mes vacías
    if raiz != DIR and not os.listdir(raiz): os.rmdir(raiz)
print(f'{juntados} archivos semestrales escritos; {borrados} diarios juntados')
