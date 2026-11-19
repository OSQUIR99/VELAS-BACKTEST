# ESTUDIOS_APERTURA_EEUU_2026_11_05

¿Se da la vuelta el S&P 500 (y BTC) tras la apertura de EE. UU.? Código del estudio del 5-nov-2026.

- `datos.py`: sesiones del S&P (1 h desde 2020) y precios de BTC (5 min) a las 9:30, 10:30 y 16:00 de Nueva York → `T1h.pkl`.
- `a1.py`: 1.ª hora frente al resto (S&P y BTC), por tamaño y por año.
- `a2.py`: S&P 15 min y 4 h (2006-26); `a3.py`: huecos de apertura; `a4.py`: reglas en % con costes.
- `lista.py`: listas `sp_manana` (seguir la mañana) y `sp_manana_contra` en formato del motor (`listas_mom/`).
- `cart.py`, `rob.py`: en la cartera (motor oficial, K8, E1 y Connors fuera del freno), vecinos, remuestreo y frenos.

Orden: `python3 datos.py && python3 lista.py && python3 cart.py`.
