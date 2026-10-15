"""Registro horario del libro de órdenes y de las liquidaciones (fuentes públicas y gratuitas, sin claves).

Qué guarda en cada ejecución (en la carpeta que se le pase, que es la rama «registro-libro» del repositorio):
  libro/AAAA-MM-DD.jsonl         una línea por fuente y moneda: mitad, horquilla, liquidez por bandas, desequilibrio,
                                 muros (los 3 tramos de 0,1 % con más dinero a cada lado) y el perfil en tramos de 0,25 %
  libro/resumen.csv              una fila por fuente y moneda con las cifras planas (para estudiarlo con pandas)
  liquidaciones/AAAA-MM-DD.csv   liquidaciones de perpetuos de OKX (BTC, ETH, SOL), sin duplicados: ts, moneda, lado, precio, usd

Fuentes: Binance contado (5.000 niveles, cubre ±1 % aprox.), OKX contado (5.000 niveles, ±1 %),
Coinbase (libro agregado entero, ±10 % y más), Hyperliquid (HYPE, 20 tramos agrupados) y liquidaciones de OKX.
Solo usa la biblioteca estándar de Python. Uso: python3 registrar_libro.py CARPETA_DATOS
"""
import csv, json, os, sys, time, urllib.request
from datetime import datetime, timezone

OUT = sys.argv[1] if len(sys.argv) > 1 else 'datos'
NOW = datetime.now(timezone.utc)
STAMP = NOW.strftime('%Y-%m-%dT%H:%M:%SZ')
DAY = NOW.strftime('%Y-%m-%d')
BANDAS = [0.5, 1, 2, 5, 10]                 # % desde la mitad
UA = {'User-Agent': 'panel-cripto-registro/1.0'}
errores = []


def get(url, data=None, timeout=40):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={**UA, **({'Content-Type': 'application/json'} if data else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def medir(fuente, moneda, bids, asks):
    """bids/asks: listas de (precio, cantidad en moneda). Devuelve el registro con bandas, muros y perfil."""
    bids = sorted(((p, q) for p, q in bids if p > 0 and q > 0), reverse=True)
    asks = sorted((p, q) for p, q in asks if p > 0 and q > 0)
    if not bids or not asks:
        raise ValueError('libro vacío')
    mid = (bids[0][0] + asks[0][0]) / 2
    rec = dict(t=STAMP, fuente=fuente, moneda=moneda, mitad=round(mid, 6),
               horquilla_pb=round((asks[0][0] - bids[0][0]) / mid * 1e4, 3),
               cubre_compras_pct=round((mid - bids[-1][0]) / mid * 100, 3),
               cubre_ventas_pct=round((asks[-1][0] - mid) / mid * 100, 3))
    for b in BANDAS:
        nb = sum(p * q for p, q in bids if (mid - p) / mid * 100 <= b)
        na = sum(p * q for p, q in asks if (p - mid) / mid * 100 <= b)
        completo = rec['cubre_compras_pct'] >= b * 0.98 and rec['cubre_ventas_pct'] >= b * 0.98
        rec[f'compras_{b}pct_usd'] = round(nb) if completo else None
        rec[f'ventas_{b}pct_usd'] = round(na) if completo else None
        rec[f'desequilibrio_{b}pct'] = round((nb - na) / (nb + na), 4) if completo and nb + na > 0 else None
    # tramos de 0,1 % (muros) y de 0,25 % (perfil), hasta ±10 %
    def tramos(nivel, ancho):
        t = {}
        for p, q in bids:
            d = (mid - p) / mid * 100
            if d <= 10: k = -int(d // ancho) - 1; t[k] = t.get(k, 0) + p * q
        for p, q in asks:
            d = (p - mid) / mid * 100
            if d <= 10: k = int(d // ancho); t[k] = t.get(k, 0) + p * q
        return t
    t1 = tramos(None, 0.1)
    vals = sorted(v for v in t1.values() if v > 0)
    mediana = vals[len(vals) // 2] if vals else 0
    def muros(lado):
        cands = [(k, v) for k, v in t1.items() if (k < 0) == (lado == 'compra') and abs(k) <= 50]   # dentro de ±5 %
        cands.sort(key=lambda kv: -kv[1])
        out = []
        for k, v in cands[:3]:
            centro = (k + 0.5) * 0.1
            out.append(dict(dist_pct=round(centro, 2), precio=round(mid * (1 + centro / 100), 6), usd=round(v),
                            veces_mediana=round(v / mediana, 1) if mediana else None))
        return out
    rec['muros_compra'] = muros('compra'); rec['muros_venta'] = muros('venta')
    rec['tramo_mediano_usd'] = round(mediana)
    t25 = tramos(None, 0.25)
    rec['perfil_025'] = {str(k): round(v) for k, v in sorted(t25.items())}
    return rec


def binance(moneda):
    j = get(f'https://data-api.binance.vision/api/v3/depth?symbol={moneda}USDT&limit=5000')
    return medir('binance_contado', moneda, [(float(p), float(q)) for p, q in j['bids']], [(float(p), float(q)) for p, q in j['asks']])


def okx(moneda):
    d = get(f'https://www.okx.com/api/v5/market/books-full?instId={moneda}-USDT&sz=5000')['data'][0]
    return medir('okx_contado', moneda, [(float(x[0]), float(x[1])) for x in d['bids']], [(float(x[0]), float(x[1])) for x in d['asks']])


def coinbase(moneda):
    j = get(f'https://api.exchange.coinbase.com/products/{moneda}-USD/book?level=2', timeout=60)
    return medir('coinbase', moneda, [(float(p), float(q)) for p, q, *_ in j['bids']], [(float(p), float(q)) for p, q, *_ in j['asks']])


def hyperliquid(moneda):
    j = get('https://api.hyperliquid.xyz/info', {'type': 'l2Book', 'coin': moneda, 'nSigFigs': 3})
    b, a = j['levels']
    return medir('hyperliquid_agrupado', moneda, [(float(x['px']), float(x['sz'])) for x in b], [(float(x['px']), float(x['sz'])) for x in a])


def liquidaciones_okx(moneda, desde_ms):
    """Pagina hacia atrás hasta llegar a lo ya guardado (máx. 15 páginas de 100)."""
    ct = float(get(f'https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId={moneda}-USDT-SWAP')['data'][0]['ctVal'])
    filas, after = [], None
    for _ in range(15):
        url = f'https://www.okx.com/api/v5/public/liquidation-orders?instType=SWAP&uly={moneda}-USDT&state=filled&limit=100'
        if after: url += f'&after={after}'
        d = get(url)['data']
        det = d[0]['details'] if d else []
        if not det: break
        for x in det:
            ts = int(x['ts'])
            if ts <= desde_ms: continue
            px, sz = float(x['bkPx']), float(x['sz'])
            filas.append(dict(ts=ts, dia=datetime.fromtimestamp(ts / 1000, timezone.utc).strftime('%Y-%m-%d'),
                              moneda=moneda, lado=x['posSide'], precio=px, usd=round(sz * ct * px)))
        oldest = min(int(x['ts']) for x in det)
        if oldest <= desde_ms: break
        after = oldest
        time.sleep(0.25)
    return filas


def main():
    os.makedirs(f'{OUT}/libro', exist_ok=True); os.makedirs(f'{OUT}/liquidaciones', exist_ok=True)
    recs = []
    tareas = [(binance, 'BTC'), (binance, 'ETH'), (okx, 'BTC'), (okx, 'ETH'), (coinbase, 'BTC'), (coinbase, 'ETH'),
              (hyperliquid, 'HYPE'), (hyperliquid, 'BTC')]
    for f, m in tareas:
        try:
            recs.append(f(m))
        except Exception as e:
            errores.append(f'{f.__name__} {m}: {type(e).__name__}: {str(e)[:120]}')
        time.sleep(0.3)
    with open(f'{OUT}/libro/{DAY}.jsonl', 'a') as fh:
        for r in recs: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    # resumen plano
    campos = ['t', 'fuente', 'moneda', 'mitad', 'horquilla_pb', 'cubre_compras_pct', 'cubre_ventas_pct'] + \
             [f'{x}_{b}pct{s}' for b in BANDAS for x, s in [('compras', '_usd'), ('ventas', '_usd'), ('desequilibrio', '')]] + \
             ['tramo_mediano_usd', 'muro_compra_dist', 'muro_compra_usd', 'muro_compra_veces', 'muro_venta_dist', 'muro_venta_usd', 'muro_venta_veces']
    nuevo = not os.path.exists(f'{OUT}/libro/resumen.csv')
    with open(f'{OUT}/libro/resumen.csv', 'a', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction='ignore')
        if nuevo: w.writeheader()
        for r in recs:
            fila = dict(r)
            for lado in ['compra', 'venta']:
                m = r[f'muros_{lado}'][0] if r[f'muros_{lado}'] else {}
                fila[f'muro_{lado}_dist'] = m.get('dist_pct'); fila[f'muro_{lado}_usd'] = m.get('usd'); fila[f'muro_{lado}_veces'] = m.get('veces_mediana')
            w.writerow(fila)
    # liquidaciones: lo nuevo desde la última guardada
    estado_f = f'{OUT}/liquidaciones/ultimo_ts.json'
    estado = json.load(open(estado_f)) if os.path.exists(estado_f) else {}
    n_liq = 0
    for m in ['BTC', 'ETH', 'SOL']:
        try:
            desde = int(estado.get(m, int(time.time() * 1000) - 2 * 3600 * 1000))
            filas = liquidaciones_okx(m, desde)
            filas.sort(key=lambda x: x['ts'])
            por_dia = {}
            for x in filas: por_dia.setdefault(x.pop('dia'), []).append(x)
            for d, xs in por_dia.items():
                f_csv = f'{OUT}/liquidaciones/{d}.csv'; nuevo_l = not os.path.exists(f_csv)
                with open(f_csv, 'a', newline='') as fh:
                    w = csv.DictWriter(fh, fieldnames=['ts', 'moneda', 'lado', 'precio', 'usd'])
                    if nuevo_l: w.writeheader()
                    w.writerows(xs)
            if filas: estado[m] = max(x['ts'] for x in filas)
            n_liq += len(filas)
        except Exception as e:
            errores.append(f'liquidaciones {m}: {type(e).__name__}: {str(e)[:120]}')
    json.dump(estado, open(estado_f, 'w'))
    with open(f'{OUT}/registro.log', 'a') as fh:
        fh.write(f'{STAMP} libros={len(recs)} liquidaciones={n_liq} errores={errores}\n')
    print(f'{STAMP}: {len(recs)} libros, {n_liq} liquidaciones nuevas, errores: {errores}')


if __name__ == '__main__':
    main()
