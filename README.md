# Registro del libro de órdenes y de las liquidaciones

Rama solo de datos. La rellena cada hora el programa `.github/workflows/libro_horario.yml` de la rama `main`
con `PANEL_CRIPTO/libro/registrar_libro.py`. Empezó el 15-oct-2026.

- `libro/AAAA-MM-DD.jsonl`: una línea por fuente y moneda en cada hora (Binance y OKX contado, Coinbase, Hyperliquid):
  mitad, horquilla, liquidez a ±0,5/1/2/5/10 %, desequilibrio, los 3 muros de cada lado (tramos de 0,1 %) y el perfil en tramos de 0,25 %.
- `libro/resumen.csv`: las cifras planas de todas las horas.
- `liquidaciones/AAAA-MM-DD.csv`: liquidaciones de perpetuos de OKX (BTC, ETH, SOL): hora en milisegundos, moneda, lado liquidado, precio y dólares.
- `registro.log`: una línea por ejecución, con los fallos.

Para qué: dentro de 6-12 meses, probar si los muros del libro y los grupos de liquidaciones anticipan algo (apartados 6.2 y 6.4).
