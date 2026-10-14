"""Convierte el JSON del día en una fila y la añade a historial/panel_diario.csv (una fila por día; si el día ya está, lo sustituye)."""
import json, sys, os
import pandas as pd

def g(d, *ks):
    for k in ks:
        if not isinstance(d, dict) or k not in d: return None
        d = d[k]
    return d

def fila(j):
    f = {'fecha_cierre_diario': j.get('fecha_cierre_diario'), 'generado_utc': j.get('generado_utc'), 'errores': len(j.get('errores') or [])}
    for s in ['BTC', 'ETH', 'HYPE']:
        t = g(j, 'tendencia', s) or {}
        for k in ['cierre', 'permiso_regimen', 'largo_1d', 'medio_4h', 'corto_1h']: f[f'{s}_{k}'] = t.get(k)
    f['prima_7d_pct'] = g(j, 'prima_coinbase', 'media_7d_pct'); f['prima_positiva'] = g(j, 'prima_coinbase', 'positiva')
    f['exceso_oi_puntos'] = g(j, 'exceso_oi', 'puntos'); f['exceso_oi_alarma'] = g(j, 'exceso_oi', 'alarma'); f['oi_fuente'] = g(j, 'exceso_oi', 'fuente')
    for s, v in (g(j, 'financiacion', 'por_activo') or {}).items():
        f[f'fin_{s}_pct8h'] = v.get('pct_8h'); f[f'fin_{s}_alarma'] = v.get('alarma')
    for s, v in (j.get('riesgo') or {}).items():
        for k, val in v.items():
            if isinstance(val, (int, float, bool, str)) or val is None: f[f'riesgo_{s}_{k}'] = val
    for k, v in (j.get('niveles_BTC') or {}).items():
        if not isinstance(v, (dict, list)): f[f'niveles_BTC_{k}'] = v
    for k in ['precio_entre_media_200_semanas', 'percentil_4_anos', 'mvrv_z', 'fecha_mvrv']: f[f'ciclo_{k}'] = g(j, 'ciclo', k)
    for k in ['semana_hasta', 'flujo_semana_M', 'semana_anterior_M', 'p90_52s_M', 'p10_52s_M', 'dos_semanas_de_salidas', 'salida_fuerte']: f[f'etf_{k}'] = g(j, 'etf', k)
    for k in ['stablecoins_30d_pct', 'miedo_y_codicia']: f[f'contexto_{k}'] = g(j, 'contexto', k)
    for s, v in (g(j, 'altcoins', 'por_moneda') or {}).items(): f[f'alt_{s}_permitida'] = v.get('permitida')
    for k, v in (j.get('fases') or {}).items():
        kk = k.replace(' ', '_').replace('(', '').replace(')', '')
        if not isinstance(v, dict): f[f'{kk}'] = v; continue
        for c in ['estado', 'suelo', 'techo', 'posicion', 'P_salida_final_alcista', 'P_rompe_arriba', 'objetivo_1_altura',
                  'ultimo_pivote', 'precio_pivote', 'r_actual', 'r_extremo']:
            if c in v: f[f'{kk}_{c}'] = v[c]
        q = v.get('calidad_ruptura')
        if q: f[f'{kk}_ruptura_celda'] = q['celda']; f[f'{kk}_ruptura_aguanta'] = q['aguanta']
    return f

if __name__ == '__main__':
    js, csv = sys.argv[1], sys.argv[2]
    r = pd.DataFrame([fila(json.load(open(js)))])
    if os.path.exists(csv):
        h = pd.read_csv(csv)
        h = h[h['fecha_cierre_diario'].astype(str) != str(r['fecha_cierre_diario'].iloc[0])]
        r = pd.concat([h, r], ignore_index=True)
    r.to_csv(csv, index=False)
    print('filas:', len(r), '· columnas:', r.shape[1])
