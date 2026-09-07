# Reparación de la migración Qt — 2026-09-07

Referencia consultada: `origin/main`, commit `dc907ca`, versión 4.2.0.

Se conservó la interfaz PySide6 y se restauraron `modifiers.py` y
`core/save_slots.py` a GitHub. Los 16 archivos de `core/*.py`, `modifiers.py`,
`save_io.py` y `game_data.py` coinciden con esa referencia, normalizando finales
de línea. No se cambiaron las reglas originales de modificación de partidas.

## Cambios corregidos

- Luchadores: conservar la selección durante la reconstrucción de la lista;
  mostrar muerte con el campo `die` del motor; usar `update_fighter` para modelos.
- Materiales: separar cantidad exacta de adición. Reducir o vaciar libera las
  referencias del Coin Locker y conserva los objetos de la bolsa. Comprobar
  capacidad antes de aumentar una cantidad exacta.
- Inventario: leer `item.items`, `part.pts`, `mushroom.msrs`, `beast.bsts` y
  `soul.cl`; mostrar ubicación, niveles y estado de cocción; conectar filtros
  y nombres con los catálogos reales.
- Calcomanías: conservar el ID premium seleccionado aunque su ficha provenga
  de la entrada estándar. Conservar selección al refrescar los catálogos de
  materiales, planos y calcomanías.
- Guardado: escribir una vez por acción; propagar y mostrar errores de
  autoguardado; sincronizar ranuras con la API original. Los diálogos trabajan
  con la partida recibida y delegan la escritura a la ventana principal.
- Revinculación: sustituir funciones inexistentes por la API original;
  trabajar sobre una copia; recuperar opciones de nombre, UID y sesión;
  validar origen/destino y manejar fallos de lectura/escritura.
- Torre y galería: utilizar directamente las funciones existentes del motor,
  eliminando los adaptadores especulativos añadidos por la migración.
- Recursos: corregir `icon_map.json`, invalidar cachés después de descargar
  o limpiar imágenes, y dirigir resultados de descargas a la pestaña vigente.
- Arranque: respetar la ruta `.sav` recibida, también después de elevar permisos;
  no ocultar errores de programación de Qt arrancando silenciosamente Tkinter.
- Tablas: impedir ediciones visuales que no persistían; conservar las acciones
  explícitas y los diálogos de doble clic.

## Validación

`python run_tests.py`: **141 pruebas, 140 aprobadas, 1 omitida, 0 errores**.
La omitida requiere una partida externa de Reddit que no existe en este equipo.

Las 18 pruebas nuevas de integración verifican contratos de las llamadas al
motor en todo `ui_qt`, selección de luchadores y catálogos, materiales,
inventario, calcomanías premium, maestría, I+D, escritura y lectura de `.sav`,
ranuras/restauración, revinculación y entrega de notificaciones del actualizador.
Las pruebas Qt existentes se aislaron de la autodetección de partidas, ranuras
y configuración reales. Se comprobaron también sintaxis, diff y renderizado
de la ventana Qt sin interacción con el juego.

El actualizador se comprobó con respuestas simuladas; no instaló cambios.
No se ejecutaron modificaciones de `masters.db` ni pruebas dentro del juego.
No se compiló un ejecutable nuevo ni se publicó en GitHub.

## Uso y respaldo

Abrir `run_editor.bat` para ejecutar el código reparado con la interfaz Qt.
La interfaz anterior sigue disponible con `python editor_gui.py --legacy-tk`.
Los ejecutables que ya estaban en `dist/` no contienen estas correcciones.

Respaldo del código previo:
`Backups/source_before_logic_repair_20260907_122043.zip`.
Resultado completo: `Backups/full_checks.log`.
Vista local de comprobación: `Backups/qt_repaired_preview.png`.
