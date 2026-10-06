# RENTA_FIJA — bonos del Tesoro de EE. UU. y puntuación 0-100

Creado el 2 de octubre de 2026. Datos hasta el 1-2 de octubre de 2026.

## Para usar cada mes
    cd "$HOME/Desktop/VELAS PARA BACKTEST/RENTA_FIJA"
    python3 score_bonos.py            # descarga datos nuevos y da la lectura de hoy
    python3 score_bonos.py --offline  # sin internet, con los ficheros de brutos/

Reglas:
- Puntuación de PLAZO >= 65 -> TLT · 35-65 -> IEF · < 35 -> SHY o BIL
- Confirmación opcional para escalonar: 10 años por debajo de su media de 10 semanas
- % acciones = 60 % + 20 % x (50 - puntuación B) / 50, entre 40 % y 80 %
- Revisar una vez al mes (semanal empeora el resultado)

## Ficheros
- `score_bonos.py` — calcula las dos puntuaciones (pandas + numpy; Python 3.9+)
- `historial_puntuaciones.csv` — puntuaciones y piezas, cada viernes desde 1966
- `semanal_precios_ajustados.csv` — cierre de cada viernes, con dividendos reinvertidos (BIL, SHV, SHY, IEI, IEF, TLH, TLT, EDV, TIP, LQD, HYG, AGG, SPY, QQQ, AGNC, NLY, GLD, JEPI, JEPQ; y cierres de DXY, VIX, MOVE, oro)
- `semanal_macro_conocido_ese_dia.csv` — datos macro tal y como se conocían ese viernes (con su retraso de publicación)
- `semanal_indicadores.csv` — los ~50 indicadores probados
- `semanal_bonos_sinteticos.csv` — rentabilidad semanal de bonos a 2, 5, 10 y 30 años reconstruida desde 1962
- `brutos/` — descargas originales (FRED, Yahoo diario, fechas de reuniones de la Fed y de publicación del IPC y del empleo)
- `estudio/` — los programas del estudio (para consulta; leen ficheros intermedios)
- `informe_termometro_bonos.html` — copia del informe

## Ojo
- Yahoo y FRED están bloqueados desde la consola de Claude; el programa funciona desde la Terminal normal de tu Mac.
- Los datos macro de FRED son la versión actual (con revisiones). Efecto pequeño, pero existe.
