# Práctica: Sistema de procesamiento de documentos con hilos y sincronización

**Asignatura:** Sistemas Operativos · Ingeniería de Sistemas

## Archivos entregados

| Archivo | Contenido |
|---|---|
| `procesamiento_pedidos.py` | Código fuente (4 hilos, `queue.Queue`, `threading.Lock`) |
| `captura_1.png` … `captura_4.png` | Cuatro ejecuciones reales del programa con total procesado y resumen por trabajador |
| `README.md` | Interpretación del comportamiento y respuestas a las preguntas |

Ejecución: `python3 procesamiento_pedidos.py` (solo biblioteca estándar).

## Diseño de la solución

- **Cola compartida:** 24 documentos `(id, tamaño)` se cargan en una `queue.Queue`.
- **4 trabajadores** (`Trabajador-1..4`): cada uno repite `get_nowait()`; si la cola está vacía se captura `queue.Empty` y el hilo termina de forma controlada.
- **Procesamiento simulado:** `time.sleep(tamaño × 0.1)`, fuera del lock para no serializar el trabajo.
- **Sección crítica:** la actualización del diccionario `resultados` (documentos y tamaño acumulado por trabajador) y del registro de IDs se hace dentro de `with lock:`.
- **Cierre:** el hilo principal hace `join()` a los cuatro hilos, imprime el resumen y ejecuta tres verificaciones automáticas.



## Interpretación del comportamiento

1. **Lo que cambia entre ejecuciones:** el orden de las líneas y cuántos documentos procesa cada trabajador. Los tamaños son aleatorios (`random.randint(1, 5)`) y el planificador del sistema operativo decide qué hilo corre en cada momento, por lo que el orden no es determinista. No se debe memorizar un orden de salida: se debe explicar por qué varía.
2. **Lo que NO cambia:** el total es siempre 24, cada ID aparece una sola vez y los cuatro hilos terminan. Esa es la corrección del programa, independiente del orden de ejecución.
3. **Reparto dinámico de carga:** no se asignan documentos fijos a cada hilo; cada trabajador toma el siguiente cuando queda libre. Por eso un trabajador que recibe documentos pequeños procesa más (p. ej. el Trabajador-1 de la captura 2 procesó 8 documentos de tamaño pequeño) y uno con documentos grandes procesa menos. En las capturas 1, 2 y 4 el tamaño acumulado por trabajador resulta parecido (≈19) porque los trabajadores quedan ocupados el mismo tiempo, que es lo que equilibra la carga.
4. **Tiempo total:** con cuatro hilos el tiempo (~1.7–2.1 s) es cercano al total de trabajo dividido entre 4. Hacerlo secuencialmente tomaría la suma de todos los tamaños × 0.1 s (≈7.5 s en la ejecución 1; estimación, no medida). La mejora es grande aquí porque `time.sleep` libera el GIL; con cálculo intensivo en Python puro (CPython) el GIL limitaría ese paralelismo, como se vio en clase.

## Respuestas a las preguntas

**1. ¿Por qué `queue.Queue` es apropiada para compartir trabajos?**
Porque es una estructura segura para hilos (thread-safe): internamente usa bloqueos, así que `put()` y `get()` son operaciones atómicas. Dos hilos nunca pueden obtener el mismo elemento, por lo que cada documento se procesa exactamente una vez, sin que tengamos que escribir sincronización adicional para repartir el trabajo. Además, `get_nowait()` combina "comprobar si hay algo" y "retirarlo" en una sola operación atómica, evitando la condición de carrera de `if not q.empty(): q.get()`, donde otro hilo podría vaciar la cola entre ambas instrucciones.

**2. ¿Qué protege `Lock` y qué pasaría si se actualizara el resumen sin él?**
Protege la sección crítica: el diccionario `resultados` (y la lista de registro), que son datos compartidos y mutables. Una actualización como `resultados[n]["docs"] += 1` es leer–modificar–escribir y no es atómica. Sin el lock, dos hilos podrían leer el mismo valor, calcular el mismo resultado y escribirlo, perdiéndose una actualización (condición de carrera). Resultado: la suma de documentos podría ser menor que 24 aunque todos se hayan procesado, el resumen sería incorrecto y variaría entre ejecuciones. Nota: en CPython, por el GIL, este fallo puede no aparecer en una sola corrida con operaciones tan simples, pero eso no lo hace correcto: el resultado depende de la implementación y del patrón de ejecución, y no es una garantía del lenguaje.

**3. ¿Qué cambiarías si cada documento tuviera que guardarse en un archivo real?**
- Cada hilo escribiría en **su propio archivo** (nombre único por ID de documento) para que no haya escritura concurrente sobre el mismo archivo; si se usara un archivo común (p. ej. un log), la escritura debería ir protegida por un lock.
- Usar `with open(...)` para garantizar el cierre y manejar excepciones (`OSError`) para que un fallo en un documento no deje el hilo en estado inconsistente ni pierda el documento (reintentar o registrar el error).
- Escribir en un archivo temporal y renombrarlo al terminar para que nunca se observe un archivo a medias (atomicidad).
- Como la E/S es lenta y libera el GIL, los hilos son especialmente adecuados; se podría aumentar el número de trabajadores, con cuidado de no saturar el disco.
- Mantener el lock solo para actualizar el resumen y no durante la escritura del archivo, para no serializar la E/S y perder el beneficio de la concurrencia.

## Reto adicional (implementado parcialmente)

- Cada trabajador acumula el **tamaño total** de documentos procesados (columna "tamaño total acumulado").
- Se registra el **tiempo total** de la versión con 4 hilos. La versión secuencial no se midió; solo se estimó (ver interpretación, punto 4).
