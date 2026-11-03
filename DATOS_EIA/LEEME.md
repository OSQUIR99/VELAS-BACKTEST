# Inventarios semanales de petróleo de la EIA

- `semanal.csv`: existencias de EE. UU. (miles de barriles) de **crudo sin la reserva estratégica**, gasolina, destilados y Cushing. Fecha = viernes de cierre de la semana; la EIA lo publica el **miércoles siguiente a las 16:30 de Madrid** (jueves si hay festivo).
- Se actualiza solo con el flujo `.github/workflows/eia_semanal.yml`: miércoles a las 16:45 y jueves a las 17:45 de Madrid (reintento), y a mano con «Run workflow».
- **Fuente pública, sin clave:** ficheros `hist_xls` de www.eia.gov. No hace falta registrarse ni poner ningún secreto.
- Lo usa el **CORTO PETRÓLEO** del bot de la cartera (`contexto-cartera/BOT/codigo/bot/cartera`), punto «inventarios bajo su media de 5 años» de la nota de escasez (documento 07). Creado el 3-nov-2026.
