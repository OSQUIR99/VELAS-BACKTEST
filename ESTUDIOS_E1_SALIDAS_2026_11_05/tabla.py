# Resumen de la cartera por montaje y salida → tabla_cartera.csv
import json, pandas as pd
F = []
for mon in ('principal', 'cripto_oficial'):
    R = json.load(open(f'res_{mon}.json'))['res']
    for s, d in R.items():
        q = d['q']
        F.append(dict(montaje=mon, salida=s,
                      ratio_todo=q[0]['ratio'], ratio_2018_21=q[1]['ratio'], ratio_2022_26=q[2]['ratio'],
                      ratio_P1_hasta_2023=d['P1']['ratio'], ratio_P2_2024_26=d['P2']['ratio'],
                      R_ano_todo=q[0]['R_ano'], R_ano_2018_21=q[1]['R_ano'], R_ano_2022_26=q[2]['R_ano'],
                      R_ano_P1=d['P1']['R_ano'], R_ano_P2=d['P2']['R_ano'],
                      caida_todo=q[0]['caida'], caida_2018_21=q[1]['caida'], caida_2022_26=q[2]['caida'],
                      caida_P1=d['P1']['caida'], caida_P2=d['P2']['caida'], media5_peores=d['media5'],
                      pasa=d.get('pasa', ''), remuestreo=d.get('boot', ''),
                      e1_tomadas=d['e1_tomadas'], e1_senales=d['e1_senales'], e1_R=d['e1_R'], e1_R_op=d['e1_R_op'],
                      e1_rech_tope20=d['e1_tope20'], e1_rech_bloque=d['e1_bloque'],
                      otras_rech_tope20=d['otros_tope20'], otras_rech_bloque=d['otros_bloque'],
                      e1_riesgo_max=d['e1_riesgo_max'], e1_n_max=d['e1_n_max'], e1_pct_dias_abierta=100 * d['e1_dias_abierta'],
                      e1_dias_3_o_mas=d['e1_dias_3omas'], e1_dias_riesgo_3R=d['e1_dias_riesgo_3R'],
                      peor_caida_desde=d['peor_caida']['desde'], peor_caida_hasta=d['peor_caida']['hasta'],
                      e1_en_peor_caida=d['peor_caida']['e1_dentro'], e1_10_peores_meses_base=d['e1_10_peores_meses']))
T = pd.DataFrame(F); T.round(3).to_csv('tabla_cartera.csv', index=False)
print(T.round(2).T.to_string())
