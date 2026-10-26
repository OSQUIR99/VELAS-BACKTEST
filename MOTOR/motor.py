# -*- coding: utf-8 -*-
"""MOTOR DE CARTERA (documento 02, P4) · 20-oct-2026.

Lee las listas de operaciones de cada familia (formato común, /home/claude/motor/listas/<familia>.parquet y
<familia>_diario.parquet) y simula la cartera completa:
  - día a día, con la cartera valorada cada día con el latente de lo abierto (caída diaria);
  - las entradas y salidas en su hora exacta (UTC) para los topes y la prioridad;
  - tope de riesgo abierto (20 R), tope por bloque con correlación (10 R, raíz de Σ Ri·Rj·ρij, ρ la mayor de 60
    sesiones y 1 año, solo con datos pasados), máximo 5 R por operación, freno de racha (4 R → × 0,5);
  - prioridad cuando entran varias a la vez, ajuste de tamaño por correlación, selección, tamaños por estrellas,
    multiplicador de R (apalancamiento), horarios de revisión e ideas de cartera (objetivo de volatilidad, freno
    con otros umbrales, reparto de riesgo entre bloques).
Unidades: R = 1 % del capital (aditivo, sin interés compuesto). Criterio: R ÷ peor caída (en R).
Solo mide el pasado. No es asesoramiento.

Uso: python3 motor.py [carpeta_listas] [carpeta_salida]
"""
import os, sys, json, heapq, math, time, glob, itertools
from collections import defaultdict
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from precios import Correlaciones

# ----------------------------------------------------------------------------------------------- parámetros
TOPE_TOTAL = 20.0
TOPE_BLOQUE = 10.0
UMBRAL_BLOQUE = 0.5
MAX_OP = 5.0
MIN_OP = 0.25
FRENO = (4.0, 0.5)
HOY = pd.Timestamp('2026-10-20')
ULT5 = HOY - pd.DateOffset(years=5)
EPOCAS = [('2018-19', '2018-01-01', '2020-01-01'), ('2020-21', '2020-01-01', '2022-01-01'),
          ('2022-23', '2022-01-01', '2024-01-01'), ('2024-26', '2024-01-01', '2026-12-31')]
HALVINGS = [pd.Timestamp('2012-11-28'), pd.Timestamp('2016-07-09'), pd.Timestamp('2020-05-11'), pd.Timestamp('2024-04-20')]
# familias cuyo riesgo abierto NO baja con el stop (stop fijo o sin stop dentro del mes)
RIESGO_FIJO = {'bolsa_e1', 'mensuales', 'c10'}
SIN_FRENO = {'shy'}             # el freno de racha no cuenta SHY (documento 00, punto 2)
FAM_INTRADIA = {'cripto'}       # señales de 4 h (en cripto no se persigue la entrada perdida)


# ----------------------------------------------------------------------------------------------- carga
def cargar(carpeta):
    ops, dias = [], []
    for p in sorted(glob.glob(os.path.join(carpeta, '*.parquet'))):
        if p.endswith('_diario.parquet'):
            continue
        fam = os.path.basename(p)[:-8]
        o = pd.read_parquet(p)
        if not len(o):
            continue
        if 'familia' not in o.columns:
            o['familia'] = fam
        o['lista'] = fam
        if 'id' not in o.columns:
            o['id'] = [f'{fam}_{i}' for i in range(len(o))]
        o['id'] = o['id'].astype(str)
        pd_ = p[:-8] + '_diario.parquet'
        if os.path.exists(pd_):
            d = pd.read_parquet(pd_)
            d['id'] = d['id'].astype(str)
            dias.append(d)
        ops.append(o)
    O = pd.concat(ops, ignore_index=True)
    D = pd.concat(dias, ignore_index=True) if dias else pd.DataFrame(columns=['id', 'fecha', 'r_latente'])
    return normalizar(O, D)


def _utc(s):
    s = pd.to_datetime(s)
    if getattr(s.dt, 'tz', None) is not None:
        s = s.dt.tz_convert('UTC').dt.tz_localize(None)
    return s


def normalizar(O, D):
    O = O.copy()
    for c in ('t_senal', 't_entrada', 't_salida'):
        if c in O.columns:
            O[c] = _utc(O[c])
    if 't_senal' not in O.columns:
        O['t_senal'] = O['t_entrada']
    O = O.dropna(subset=['t_entrada', 't_salida', 'r_final']).copy()
    O.loc[O.t_salida < O.t_entrada, 't_salida'] = O.t_entrada
    for c, v in (('tam_R', 1.0), ('estrellas', np.nan), ('direccion', 1), ('bloque', 'otros'), ('mae_R', np.nan),
                 ('mfe_R', np.nan), ('motivo_salida', ''), ('r_bruto', np.nan)):
        if c not in O.columns:
            O[c] = v
    O['tam_R'] = O['tam_R'].astype(float).fillna(1.0)
    O.loc[O.tam_R <= 0, 'tam_R'] = np.nan
    O = O.dropna(subset=['tam_R'])
    O['r_final'] = O['r_final'].astype(float)
    O['direccion'] = O['direccion'].fillna(1).astype(int)
    if 'riesgo_inicial_R' not in O.columns:
        O['riesgo_inicial_R'] = O['tam_R']
        if 'promedio_maximo_R' in O.columns:
            # promediado pendiente: cuenta como si se llenara (pérdida máxima 1,25 × tamaño; documento 00, punto 7)
            pm = O['promedio_maximo_R'].astype(float)
            m = pm.notna() & (pm > O['tam_R'] + 1e-9)
            O.loc[m, 'riesgo_inicial_R'] = 1.25 * O.loc[m, 'tam_R']
    O['riesgo_inicial_R'] = O['riesgo_inicial_R'].astype(float).fillna(O['tam_R'])
    if 'senal' not in O.columns:
        O['senal'] = O['lista']
    O['senal'] = O['senal'].fillna(O['lista']).astype(str)
    if 'nota' not in O.columns:
        O['nota'] = np.nan
    # calidad propia de cada familia: la nota de puntos si la hay (+0,1 × estrellas para desempatar), si no estrellas
    est = O['estrellas'].astype(float)
    O['calidad'] = est
    if 'puntos' in O.columns:
        pu = pd.to_numeric(O['puntos'], errors='coerce')
        m = pu.notna()
        O.loc[m, 'calidad'] = pu[m] + 0.1 * est[m].fillna(0)
    m = O['calidad'].isna() & O['nota'].notna()
    O.loc[m, 'calidad'] = O.loc[m, 'nota'].astype(float)
    O['calidad'] = O['calidad'].fillna(3.0)
    if 'operable' in O.columns:
        O['operable'] = O['operable'].fillna(True).astype(bool)
    else:
        O['operable'] = True
    O = O.sort_values(['t_entrada', 'id']).reset_index(drop=True)
    O['k'] = np.arange(len(O))
    # ---- diario
    D = D.copy()
    D['fecha'] = _utc(D['fecha']).dt.normalize()
    D = D[D.id.isin(set(O.id))]
    # escala del latente: ¿en R finales (× tam_R) o en R de la operación?
    escala = {}
    ult = D.sort_values('fecha').groupby('id').last()
    j = O.set_index('id')[['r_final', 'tam_R', 'lista']].join(ult[['r_latente']], how='inner')
    for fam, g in j.groupby('lista'):
        g = g[(g.tam_R - 1).abs() > 1e-6]
        if not len(g):
            escala[fam] = 'final'
            continue
        ef = np.nanmean(np.abs(g.r_latente - g.r_final))
        eu = np.nanmean(np.abs(g.r_latente - g.r_final / g.tam_R))
        escala[fam] = 'final' if ef <= eu else 'unidad'
    O['escala_diario'] = O['lista'].map(escala).fillna('final')
    return O, D


def preparar_series(O, D, dia0):
    """Por operación: índices de día (desde dia0), latente en R finales (lista) y riesgo en R finales."""
    lat = {}
    idx_id = dict(zip(O.id, O.k))
    tam = O.tam_R.values
    esc = O.escala_diario.values
    tienen_riesgo = 'riesgo_R' in D.columns
    for oid, g in D.sort_values('fecha').groupby('id', sort=False):
        k = idx_id[oid]
        d = ((g.fecha.values - dia0) / np.timedelta64(1, 'D')).astype(int)
        v = g.r_latente.values.astype(float)
        if esc[k] == 'unidad':
            v = v * tam[k]
        r = g.riesgo_R.values.astype(float) if tienen_riesgo else None
        if r is not None and esc[k] == 'unidad':
            r = r * tam[k]
        lat[k] = (d, v, r)
    return lat


# ----------------------------------------------------------------------------------------------- motor
class Motor:
    def __init__(self, O, D, corr=None, desde=None, hasta=None):
        self.O0 = O
        self.D = D
        self.dia0 = np.datetime64(pd.Timestamp(O.t_entrada.min()).normalize())
        self.lat = preparar_series(O, D, self.dia0)
        fin = max(O.t_salida.max(), HOY)
        self.ndias = int((np.datetime64(pd.Timestamp(fin).normalize()) - self.dia0) / np.timedelta64(1, 'D')) + 2
        self.corr = corr
        n = len(O)
        self.ent_dia = ((O.t_entrada.dt.normalize().values - self.dia0) / np.timedelta64(1, 'D')).astype(int)
        self.sal_dia = ((O.t_salida.dt.normalize().values - self.dia0) / np.timedelta64(1, 'D')).astype(int)
        self.t_ent = O.t_entrada.values
        self.t_sal = O.t_salida.values
        self.rf = O.r_final.values.astype(float)
        self.tam = O.tam_R.values.astype(float)
        self.r0 = O.riesgo_inicial_R.values.astype(float)
        self.dir = O.direccion.values.astype(int)
        self.act = np.array([str(x) for x in O.activo], dtype=object)
        self.fam = np.array([str(x) for x in O.lista], dtype=object)
        self.blo = np.array([str(x) for x in O.bloque], dtype=object)
        # posición en días hábiles de cada entrada (para la correlación con datos anteriores)
        self.tb = (np.array([corr.t_de(x) for x in O.t_entrada]) if corr is not None else np.zeros(len(O), int))
        self.cal = O.calidad.values.astype(float)
        self.fijo = np.array([f in RIESGO_FIJO for f in self.fam])
        self.sin_freno = np.array([f in SIN_FRENO for f in self.fam])
        # riesgo aproximado si la lista no trae riesgo_R: el stop sube con el máximo latente (≥ +1 R → 0)
        self.mfe_run = {}
        for k, (d, v, r) in self.lat.items():
            if r is None:
                u = v / max(self.tam[k], 1e-9)
                self.mfe_run[k] = np.maximum.accumulate(np.maximum(u, 0))

    # riesgo abierto (en R finales de la lista) de la operación k el día anterior a `dia`
    def riesgo(self, k, dia):
        if k not in self.lat:
            return self.r0[k]
        d, v, r = self.lat[k]
        i = int(np.searchsorted(d, dia, side='left')) - 1
        if i < 0:
            return self.r0[k]
        if r is not None:
            return float(r[i])
        if self.fijo[k]:
            return self.r0[k]
        return self.r0[k] * max(0.0, 1.0 - float(self.mfe_run[k][i]))

    def latente(self, k, dia):
        if k not in self.lat:
            return 0.0
        d, v, r = self.lat[k]
        i = int(np.searchsorted(d, dia, side='left')) - 1
        return float(v[i]) if i >= 0 else 0.0

    def simular(self, cfg=None, mascara=None):
        cfg = dict(cfg or {})
        tope_t = cfg.get('tope_total', TOPE_TOTAL)
        tope_b = cfg.get('tope_bloque', TOPE_BLOQUE)
        umbral = cfg.get('umbral_bloque', UMBRAL_BLOQUE)
        max_op = cfg.get('max_op', MAX_OP)
        freno = cfg.get('freno', FRENO)
        mult = cfg.get('mult', 1.0)
        tam_mult = cfg.get('tam_mult')          # vector por operación
        prioridad = cfg.get('prioridad', 'llegada')
        agrupar = cfg.get('agrupar', 'hora')
        ajuste = cfg.get('ajuste_corr')         # None, 'raiz', 'lineal'
        modo = cfg.get('modo_tope', 'rechazar')
        vol_obj = cfg.get('vol_obj')            # dict(obj=, ventana=, lim=(0.5,1.5))
        pesos_bloque = cfg.get('pesos_bloque')  # dict bloque->peso (o función(dia)->dict)
        shy_fuera = cfg.get('shy_fuera_tope', False)
        freno_modo = cfg.get('freno_modo', 'cerrado')   # 'cerrado' (vigente) o 'latente' (cerrado + abierto valorado)
        pico_l = 0.0
        n = len(self.rf)
        cand = np.ones(n, bool) if mascara is None else np.asarray(mascara, bool).copy()
        idxs = np.flatnonzero(cand)
        s = np.zeros(n)
        motivo = np.array([''] * n, dtype=object)
        abiertas = {}            # k -> tamaño s
        salidas = []             # heap (t_salida, k)
        cerrado = 0.0
        pico = 0.0
        # para el objetivo de volatilidad: serie diaria del resultado de la cartera (en R) hasta ayer
        eq_dia = np.zeros(self.ndias) if vol_obj else None
        if agrupar == 'dia':
            claves = self.ent_dia[idxs]
        else:
            claves = (self.t_ent[idxs].astype('datetime64[h]')).astype(np.int64)
        pos = 0
        N = len(idxs)
        perdidas = defaultdict(int)
        while pos < N:
            q = pos
            while q < N and claves[q] == claves[pos]:
                q += 1
            grupo = list(idxs[pos:q])
            pos = q
            t = self.t_ent[grupo[0]]
            dia = self.ent_dia[grupo[0]]
            # cerrar lo que sale antes
            while salidas and salidas[0][0] <= t:
                ts, k = heapq.heappop(salidas)
                if k in abiertas:
                    sz = abiertas.pop(k)
                    if not self.sin_freno[k]:
                        cerrado += sz * self.rf[k]
                        pico = max(pico, cerrado)
            if freno and freno_modo == 'latente':
                eq_l = cerrado + sum(abiertas[j] * self.latente(j, dia) for j in abiertas if not self.sin_freno[j])
                pico_l = max(pico_l, eq_l)
                f_freno = freno[1] if pico_l - eq_l >= freno[0] else 1.0
            else:
                f_freno = freno[1] if (freno and pico - cerrado >= freno[0]) else 1.0
            f_vol = 1.0
            if vol_obj:
                f_vol = self._factor_vol(abiertas, dia, vol_obj)
            # orden dentro del grupo
            if len(grupo) > 1 and prioridad != 'llegada':
                grupo = self._ordenar(grupo, abiertas, prioridad, self.tb[grupo[0]])
            for k in grupo:
                base = mult * (tam_mult[k] if tam_mult is not None else 1.0)
                if pesos_bloque is not None:
                    pb = pesos_bloque(dia) if callable(pesos_bloque) else pesos_bloque
                    base *= pb.get(self.blo[k], 1.0)
                sz = base * (f_freno if not self.sin_freno[k] else 1.0) * (f_vol if not self.sin_freno[k] else 1.0)
                if ajuste and abiertas:
                    sz *= self._f_ajuste(k, abiertas, self.tb[k], ajuste)
                if max_op and sz * self.tam[k] > max_op:
                    sz = max_op / self.tam[k]
                if sz <= 0:
                    motivo[k] = 'tamaño 0'
                    continue
                r_new = sz * self.r0[k]
                cuenta_total = not (shy_fuera and self.fam[k] == 'shy')
                if tope_t is not None and cuenta_total:
                    usado = sum(abiertas[j] * self.riesgo(j, dia) for j in abiertas
                                if not (shy_fuera and self.fam[j] == 'shy'))
                    libre = tope_t - usado
                    if r_new > libre + 1e-9:
                        if modo == 'recortar' and libre * self.tam[k] / self.r0[k] >= MIN_OP:
                            sz = libre / self.r0[k]
                            r_new = libre
                        else:
                            motivo[k] = 'tope 20 R'
                            perdidas['total'] += 1
                            continue
                if tope_b is not None and abiertas:
                    jr = self._riesgo_bloque(k, sz, abiertas, self.tb[k], dia, umbral)
                    if jr > tope_b + 1e-9:
                        if modo == 'recortar':
                            # buscar el tamaño que cabe (bisección)
                            lo, hi = 0.0, sz
                            for _ in range(20):
                                mid = (lo + hi) / 2
                                if self._riesgo_bloque(k, mid, abiertas, self.tb[k], dia, umbral) <= tope_b:
                                    lo = mid
                                else:
                                    hi = mid
                            if lo * self.tam[k] >= MIN_OP:
                                sz = lo
                            else:
                                motivo[k] = 'tope bloque'
                                perdidas['bloque'] += 1
                                continue
                        else:
                            motivo[k] = 'tope bloque'
                            perdidas['bloque'] += 1
                            continue
                s[k] = sz
                abiertas[k] = sz
                heapq.heappush(salidas, (self.t_sal[k], k))
        return Resultado(self, s, motivo, cfg, cand)

    def _rho(self, a, b, t):
        # t = posición en días hábiles (self.tb[k] de la operación que entra)
        if self.corr is None:
            return 1.0 if a == b else 0.3
        return self.corr.rho_t(a, b, t)

    def _riesgo_bloque(self, k, sz, abiertas, t, dia, umbral):
        miembros = [(k, sz * self.r0[k])]
        for j, sj in abiertas.items():
            rj = sj * self.riesgo(j, dia)
            if rj <= 0:
                continue
            rho = self._rho(self.act[k], self.act[j], t) * self.dir[k] * self.dir[j]
            if rho >= umbral:
                miembros.append((j, rj))
        if len(miembros) == 1:
            return miembros[0][1]
        tot = 0.0
        for (a, ra), (b, rb) in itertools.product(miembros, miembros):
            rho = 1.0 if a == b else self._rho(self.act[a], self.act[b], t) * self.dir[a] * self.dir[b]
            tot += ra * rb * rho
        return math.sqrt(max(tot, 0.0))

    def _f_ajuste(self, k, abiertas, t, modo):
        # número efectivo de operaciones abiertas que apuestan a lo mismo (correlación de posición > 0)
        ne = 0.0
        for j in abiertas:
            rho = self._rho(self.act[k], self.act[j], t) * self.dir[k] * self.dir[j]
            if rho > 0:
                ne += rho
        if modo == 'raiz':
            return 1.0 / math.sqrt(1.0 + ne)
        return 1.0 / (1.0 + ne)

    def _ordenar(self, grupo, abiertas, prioridad, t):
        if prioridad == 'calidad':
            return sorted(grupo, key=lambda k: (-self.cal[k], -self.tam[k], k))
        if prioridad in ('descorr', 'inversa'):
            def clave(k):
                if not abiertas:
                    return 0.0
                rs = [self._rho(self.act[k], self.act[j], t) * self.dir[k] * self.dir[j] for j in abiertas]
                return max(rs) if prioridad == 'descorr' else sum(rs)
            return sorted(grupo, key=lambda k: (clave(k), k))
        return grupo

    def _factor_vol(self, abiertas, dia, vol_obj):
        # volatilidad de la cartera estimada con el riesgo abierto: no hace falta la curva (evita circularidad)
        # objetivo: riesgo abierto total ≈ obj; si hay mucho abierto, lo nuevo más pequeño
        usado = sum(abiertas[j] * self.riesgo(j, dia) for j in abiertas)
        obj = vol_obj['obj']
        f = obj / max(usado, 1e-9) if usado > obj else vol_obj.get('max', 1.0)
        lo, hi = vol_obj.get('lim', (0.5, 1.5))
        return float(min(hi, max(lo, f)))

    # curva diaria de una selección de operaciones con tamaños s
    def curva(self, s, mascara=None):
        sel = np.flatnonzero(s > 0) if mascara is None else np.flatnonzero((s > 0) & mascara)
        delta = np.zeros(self.ndias + 1)
        for k in sel:
            sk = s[k]
            if k in self.lat:
                d, v, _ = self.lat[k]
                m = d < self.sal_dia[k]
                dd, vv = d[m], v[m]
                if len(dd):
                    np.add.at(delta, dd, sk * np.diff(np.r_[0.0, vv]))
                    delta[self.sal_dia[k]] += sk * (self.rf[k] - vv[-1])
                else:
                    delta[self.sal_dia[k]] += sk * self.rf[k]
            else:
                delta[self.sal_dia[k]] += sk * self.rf[k]
        eq = np.cumsum(delta)[:self.ndias]
        return pd.Series(eq, index=pd.date_range(pd.Timestamp(self.dia0), periods=self.ndias, freq='D'))


class Resultado:
    def __init__(self, M, s, motivo, cfg, cand):
        self.M, self.s, self.motivo, self.cfg, self.cand = M, s, motivo, cfg, cand
        self._eq = None

    @property
    def eq(self):
        if self._eq is None:
            self._eq = self.M.curva(self.s)
        return self._eq

    def metricas(self, desde=None, hasta=None, mascara=None, eq=None):
        return metricas(self.M, self.s, desde, hasta, mascara, eq if eq is not None else
                        (self.eq if mascara is None else self.M.curva(self.s, mascara)))


def caida_max(e):
    if len(e) == 0:
        return 0.0
    pk = np.maximum.accumulate(np.r_[0.0, e.values - e.values[0]])[1:]
    return float((pk - (e.values - e.values[0])).max())


def metricas(M, s, desde=None, hasta=None, mascara=None, eq=None):
    desde = pd.Timestamp(desde) if desde is not None else pd.Timestamp(M.dia0)
    hasta = pd.Timestamp(hasta) if hasta is not None else HOY + pd.Timedelta(days=1)
    ent = pd.DatetimeIndex(M.t_ent)
    sel = (s > 0) & (ent >= desde) & (ent < hasta)
    if mascara is not None:
        sel &= mascara
    if eq is None:
        eq = M.curva(s, mascara)
    e = eq[(eq.index >= desde - pd.Timedelta(days=1)) & (eq.index < hasta)]
    e = e[e.index <= HOY]
    anos = max((min(hasta, HOY) - desde).days / 365.25, 1e-9)
    rt = float(e.iloc[-1] - e.iloc[0]) if len(e) else 0.0
    dd = caida_max(e)
    r = s[sel] * M.rf[sel]
    meses = pd.period_range(desde, min(hasta, HOY) - pd.Timedelta(days=1), freq='M')
    cuenta = pd.Series(1, index=ent[sel].to_period('M')).groupby(level=0).sum().reindex(meses, fill_value=0)
    return dict(n=int(sel.sum()), ops_mes_media=float(cuenta.mean()) if len(cuenta) else 0.0,
                ops_mes_mediana=float(cuenta.median()) if len(cuenta) else 0.0,
                meses_sin=int((cuenta == 0).sum()), meses=int(len(cuenta)),
                R_total=rt, R_ano=rt / anos, caida=dd, R_op=float(r.mean()) if len(r) else 0.0,
                acierto=float((r > 0).mean()) if len(r) else 0.0,
                R_caida=rt / dd if dd > 1e-9 else np.nan, Rano_caida=(rt / anos) / dd if dd > 1e-9 else np.nan,
                R_abierto_max=None)


def fase_ciclo_cripto(t):
    """24-36 meses tras el halving (el tramo de hoy: abr-2026 a abr-2027)."""
    for h in HALVINGS:
        if h + pd.DateOffset(months=24) <= t < h + pd.DateOffset(months=36):
            return True
    return False
