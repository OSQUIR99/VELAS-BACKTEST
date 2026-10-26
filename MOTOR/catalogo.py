# -*- coding: utf-8 -*-
"""Junta las tablas del motor de cartera en CATALOGO.md (lectura cruda) y copia CSV y código a la carpeta de Drive
pendiente. Uso: python3 catalogo.py <carpeta_salida> <carpeta_drive>"""
import os, sys, glob, shutil, json
import pandas as pd

TITULOS = [
    ('p1_total.csv', '1 · Estadística base «si se hubieran ejecutado todas» (sin topes ni freno): total'),
    ('p1_epocas.csv', '1 · Total por épocas (cartera, ventana común)'),
    ('p1_por_familia_ventana.csv', '1 · Por familia, ventana común de la cartera'),
    ('p1_por_familia_historia.csv', '1 · Por familia, toda su historia'),
    ('p1_por_senal.csv', '1 · Por señal, toda su historia'),
    ('p1_fase_actual.csv', '1 · Fase actual (misma fase del activo con su media de 200; tramo 24-36 meses del halving) y últimos 5 años por familia'),
    ('p1_por_activo.csv', '1 · Por activo (toda su historia, 5 operaciones o más)'),
    ('p2_topes.csv', '2 · Con y sin topes'),
    ('p2_perdidas_por_familia.csv', '2 · Señales perdidas por los topes, por familia (R a tamaño de la lista)'),
    ('p2b_variantes.csv', '2 · La cartera vigente cambiando la cripto por sus variantes (24 h, propuesta de SOL y LINK)'),
    ('p3_prioridad.csv', '3 · Prioridad cuando entran varias a la vez y tamaño ajustado por correlación'),
    ('p4_seleccion.csv', '4 · Selección (walk-forward y reglas fijas aplicadas año a año)'),
    ('p4_seleccion_elecciones.csv', '4 · Qué regla eligió el walk-forward cada año (R/año ÷ caída dentro de muestra)'),
    ('p5_tamanos.csv', '5 · Tamaños proporcionales a las estrellas'),
    ('p5_tamanos_elecciones.csv', '5 · Qué esquema eligió el walk-forward cada año'),
    ('p6_apalancamiento_con_topes.csv', '6 · Multiplicador de R con topes (rejilla) y multiplicador que lleva la peor caída a 20 y 30 R'),
    ('p6_combinaciones_sin_topes.csv', '6 · Combinaciones de familias sin topes: multiplicador que aguanta cada una'),
    ('p7_horario.csv', '7 · Horario de revisiones'),
    ('p7_simulador_rebote4h_horario.csv', '7 · Estimación con el simulador provisional del REBOTE 4H (subida del stop y salidas)'),
    ('p8_ideas.csv', '8 · Ideas de cartera: dentro de muestra (hasta 2021) y fuera de muestra (2022-26)'),
    ('p8_pesos_bloque.csv', '8 · Pesos por bloque del reparto de riesgo (año a año)'),
    ('p8b_ideas.csv', '8 · Segunda tanda: topes distintos, freno con la cartera valorada, peso por familia'),
    ('p8b_pesos_familia.csv', '8 · Pesos por familia (R/año ÷ caída de los 3 años anteriores, 0,5-2)'),
    ('p9_combinaciones_finales.csv', '9 · Combinaciones finales: dentro/fuera de muestra, épocas, últimos 5 años y multiplicador para 20 y 30 R de caída'),
    ('p9_familias_antes_de_2018.csv', '9 · Cada familia antes de 2018 (para ver si la exclusión se podía decidir antes)'),
]


def md(df, maxfilas=400):
    df = df.head(maxfilas)
    cols = [str(c) for c in df.columns]
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in df.iterrows():
        out.append('| ' + ' | '.join('' if (isinstance(v, float) and pd.isna(v)) else str(v) for v in r.values) + ' |')
    return '\n'.join(out)


def main(sal, drive):
    os.makedirs(os.path.join(drive, 'codigo'), exist_ok=True)
    os.makedirs(os.path.join(drive, 'csv'), exist_ok=True)
    partes = ['# CATÁLOGO · Motor de cartera (20-oct-2026)\n',
              'Lectura cruda: todas las tablas tal cual salen del motor, sin omitir filas por umbral. '
              'R = 1 % del capital (aditivo). Caída = peor caída de la cartera valorada cada día con el latente. '
              '«R/año ÷ caída» es el criterio de Óscar. Solo mide el pasado; no es asesoramiento.\n',
              'Columnas: n = operaciones; ops_mes = operaciones al mes; meses_sin = meses sin ninguna; R_total; R_ano; '
              'caida; R_op = R por operación; acierto; R_caida = R total ÷ caída; Rano_caida = R al año ÷ caída; '
              'ep_* = R al año ÷ caída de cada época; *_OOS = fuera de muestra; *_IS = dentro de muestra.\n']
    for f, t in TITULOS:
        p = os.path.join(sal, f)
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        partes.append(f'\n## {t}\n\nArchivo: `csv/{f}` ({len(df)} filas)\n\n' + md(df) + '\n')
        shutil.copy(p, os.path.join(drive, 'csv', f))
    for f in glob.glob(os.path.join(sal, '*.csv')):
        shutil.copy(f, os.path.join(drive, 'csv', os.path.basename(f)))
    open(os.path.join(drive, 'CATALOGO.md'), 'w').write('\n'.join(partes))
    aq = os.path.dirname(os.path.abspath(__file__))
    for f in ('motor.py', 'precios.py', 'analisis.py', 'horario.py', 'extra.py', 'recomendacion.py', 'catalogo.py',
              'provisional/gen.py'):
        shutil.copy(os.path.join(aq, f), os.path.join(drive, 'codigo', os.path.basename(f)))
    for f in glob.glob(os.path.join(sal, '*.json')):
        shutil.copy(f, os.path.join(drive, os.path.basename(f)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
