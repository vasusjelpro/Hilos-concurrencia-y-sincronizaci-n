
import threading
import queue
import time
import random

NUM_DOCUMENTOS = 24
NUM_TRABAJADORES = 4

trabajos = queue.Queue()
resultados = {}          
registro_ids = []       
lock = threading.Lock()


for doc_id in range(1, NUM_DOCUMENTOS + 1):
    trabajos.put((doc_id, random.randint(1, 5)))


def trabajador(nombre):
    """Retira documentos de la cola hasta que esté vacía."""
    while True:
        try:
           
            doc_id, tamano = trabajos.get_nowait()
        except queue.Empty:
            break  

        
        time.sleep(tamano * 0.1)
        print(f"{nombre} procesó documento {doc_id:02d} (tamaño {tamano})")

        
        with lock:
            resultados[nombre]["docs"] += 1
            resultados[nombre]["tamano"] += tamano
            registro_ids.append((nombre, doc_id))


def main():
    inicio = time.perf_counter()

    hilos = []
    for i in range(1, NUM_TRABAJADORES + 1):
        nombre = f"Trabajador-{i}"
        resultados[nombre] = {"docs": 0, "tamano": 0}
        h = threading.Thread(target=trabajador, args=(nombre,), name=nombre)
        hilos.append(h)

    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    duracion = time.perf_counter() - inicio

    # ---- Resumen ----
    print("\n===== RESUMEN POR TRABAJADOR =====")
    for nombre, datos in sorted(resultados.items()):
        print(f"{nombre}: {datos['docs']:2d} documentos | tamaño total acumulado: {datos['tamano']}")

    total = sum(d["docs"] for d in resultados.values())
    print(f"\nTOTAL PROCESADO: {total} de {NUM_DOCUMENTOS}")

    # ---- Verificaciones ----
    ids = [doc for _, doc in registro_ids]
    v1 = total == NUM_DOCUMENTOS
    v2 = len(ids) == len(set(ids)) == NUM_DOCUMENTOS
    v3 = all(not h.is_alive() for h in hilos)
    print("\n===== VERIFICACIONES =====")
    print(f"1. Suma de documentos == {NUM_DOCUMENTOS}:      {'OK' if v1 else 'FALLO'}")
    print(f"2. Cada ID procesado una sola vez:   {'OK' if v2 else 'FALLO'}")
    print(f"3. Los 4 hilos terminaron:           {'OK' if v3 else 'FALLO'}")
    print(f"\nTiempo total (4 hilos): {duracion:.2f} s")


if __name__ == "__main__":
    main()
