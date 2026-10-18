# Documento de Diseño — Triage Queue

## Elección de la Estructura de Datos Interna: Tres Deques Separados

La cola interna utiliza **tres instancias de `collections.deque`**, una por nivel de triaje (1, 2 y 3). Se optó por este enfoque tras evaluar las siguientes alternativas:

### Alternativa 1: Un único `deque` con inserción ordenada
Insertar cada paciente en la posición que le corresponde según nivel de triaje y luego hora de llegada.

| Criterio | Deque ordenado único | Tres deques |
|---|---|---|
| Encolar | O(n) — hay que encontrar la posición de inserción | **O(1)** — siempre `append` al deque correcto |
| Desencolar | O(1) — `popleft` | **O(1)** — revisar 3 deques, `popleft` del primero no vacío |
| Peek | O(1) | **O(1)** |
| list_queue | O(n) | **O(n)** |
| stats | O(n) — hay que recorrer y contar | **O(1)** — `len()` de cada deque |
| Complejidad de implementación | Baja | Baja |

**Veredicto**: Tres deques ganan en encolar y stats. Como el enunciado menciona explícitamente la concurrencia entre encolar/desencolar, el O(1) en encolado es la opción más segura — no hay un paso de ordenamiento que pueda generar condiciones de carrera o requiera un candado entre operaciones.

### Alternativa 2: Una sola cola de prioridad con `heapq`
Usar el módulo `heapq` con una tupla `(prioridad, contador_llegada, paciente)`.

| Criterio | `heapq` | Tres deques |
|---|---|---|
| Encolar | O(log n) — push al heap | **O(1)** — `append` |
| Desencolar | O(log n) — pop del heap | **O(1)** — `popleft` |
| Peek | O(1) — acceder a `heap[0]` | **O(1)** |
| list_queue | O(n log n) — hay que ordenar o copiar el heap | **O(n)** — solo concatenar tres deques |
| stats | O(n) — recorrer todos los elementos | **O(1)** — `len()` de cada deque |
| Orden entre igual prioridad | Requiere contador explícito para desempatar | **Natural** — los elementos ya están en orden FIFO |

**Veredicto**: `heapq` es teóricamente elegante pero es estrictamente más lento en todas las operaciones excepto peek. En un sistema de triaje con alto rendimiento, es preferible O(1) en encolar y desencolar. Además, `heapq` no preserva de forma nativa el orden de inserción para elementos de igual prioridad — hay que llevar un contador incremental manualmente, lo que añade complejidad.

### Alternativa 3: Tres listas usadas como colas
Usar tres objetos `list` de Python, simulando una cola con `list.append` + `list.pop(0)`.

| Criterio | Lista como cola | Tres deques |
|---|---|---|
| Encolar | O(1) — amortizado | O(1) |
| Desencolar | **O(n)** — `pop(0)` desplaza todos los elementos | **O(1)** — `popleft` |
| Peek | O(1) | O(1) |
| list_queue | O(n) | O(n) |
| stats | O(1) | O(1) |

**Veredicto**: `list.pop(0)` es O(n) porque cada elemento subsiguiente debe ser reubicado. Esto es inaceptable para un sistema en tiempo real.

### Enfoque elegido: Tres instancias de `collections.deque`

```
self._queues = {
    1: deque(),   # Crítico
    2: deque(),   # Urgente
    3: deque(),   # Estándar
}
```

- **Encolar** (`enqueue`): O(1) — `append` al deque del nivel correspondiente.
- **Desencolar** (`dequeue`): O(1) — revisar deques 1→2→3; `popleft` del primero no vacío.
- **Peek** (`peek`): O(1) — índice `[0]` sobre el primer deque no vacío.
- **Listar cola** (`list_queue`): O(n) — concatenar los tres deques en orden.
- **Estadísticas** (`stats`): O(1) — tres llamadas a `len()`.

El diseño de tres deques aplica la regla de ordenamiento de forma natural, sin lógica de ordenación ni desempate: el nivel 1 se revisa siempre primero, luego el 2, luego el 3. Dentro de cada deque, los elementos están en orden FIFO estricto porque solo usamos `append` por la derecha y `popleft` por la izquierda.

---

## Concurrencia: Condiciones de Carrera y Doble Procesamiento

La implementación actual es monohilo con una interfaz CLI, por lo que no hay acceso concurrente. Sin embargo, si esta cola se integrara en un servicio multi-worker (p. ej., varias enfermeras de triaje o un servidor web asíncrono), deben abordarse las **condiciones de carrera**.

### El problema

Considera dos operaciones concurrentes:

1. **Worker A** llama a `dequeue()` — extrae y devuelve el siguiente paciente, digamos `Paciente X` (nivel 1).
2. **Worker B** llama a `enqueue()` — añade un nuevo paciente crítico `Paciente Y` (nivel 1).

Sin sincronización, es posible el siguiente intercalado:

| Tiempo | Worker A (dequeue) | Worker B (enqueue) |
|---|---|---|
| T1 | Lee `len(self._queues[1])` → 1 | — |
| T2 | — | `self._queues[1].append(Y)` |
| T3 | `self._queues[1].popleft()` → devuelve X | — |

En **T2**, el deque tiene `[Y]` (X sigue ahí si popleft aún no se ejecutó, o X ya no está e Y está). En **T3**, Worker A obtiene X, lo cual es correcto. **¿Pero qué pasa en el orden inverso?**

| Tiempo | Worker A (dequeue) | Worker B (enqueue) |
|---|---|---|
| T1 | — | `self._queues[1].append(Y)` |
| T2 | `self._queues[1].popleft()` → devuelve Y | — |
| T3 | `if self.is_empty(): ...` | — |

Aquí, Worker A desencola **Y, no X**. El Paciente X (que llegó antes y también es crítico) queda esperando mientras Y es atendido primero, violando la garantía FIFO dentro del mismo nivel de triaje.

**Aún más crítico**, considera `dequeue()` intercalado consigo mismo:

| Tiempo | Worker A (dequeue) | Worker B (dequeue) |
|---|---|---|
| T1 | Lee `self._queues[1]` → tiene X | Lee `self._queues[1]` → tiene X |
| T2 | `self._queues[1].popleft()` → X | — |
| T3 | — | `self._queues[1].popleft()` → Y |

Ambos workers leen el mismo estado y ambos creen haber obtenido el paciente correcto. **El Paciente X se procesa dos veces** — un error crítico en un sistema médico.

### Solución: Mutex (threading.Lock) con un protocolo de tres fases

Para un despliegue multi-hilo o multi-proceso, cada método público (especialmente `enqueue`, `dequeue`, `peek`, `list_queue`, `stats`) debe adquirir un **candado (lock)** (`threading.Lock`) que proteja los deques internos.

El orden correcto de mutación para un `dequeue()` seguro es:

```
1. ADQUIRIR LOCK
2. VERIFICAR is_empty  →  si está vacío, LANZAR IndexError (o devolver centinela)
3. DETERMINAR objetivo: recorrer self._queues[1], [2], [3] hasta el primer deque no vacío
4. PACIENTE = objetivo.popleft()   ← paso atómico único bajo lock
5. LIBERAR LOCK
6. DEVOLVER PACIENTE
```

Los pasos 2–4 ocurren **bajo una única adquisición del lock**. Ninguna otra lectura o escritura puede intercalarse. Esto garantiza:

- **Sin doble procesamiento**: Dos llamadas concurrentes a `dequeue()` verán estado consistente — la primera extrae X, la segunda ve el deque de nivel 1 vacío (o sin más pacientes críticos) y procede con el siguiente paciente en el orden correcto. Ambas llamadas no pueden obtener el mismo paciente.
- **Orden correcto**: Si un paciente crítico Y llega mientras se está desencolando X, ocurre una de dos:
  - El enqueue adquiere el lock **antes** que el dequeue → Y se coloca en el deque, luego el dequeue lo lee y devuelve Y primero (si X ya fue desencolado por otro worker, o devuelve X primero si no).
  - El enqueue adquiere el lock **después** que el dequeue → X es desencolado, luego Y es añadido. El orden se preserva.
- **Sin espera activa**: El lock se libera inmediatamente después de la mutación; la contención es mínima.

### Alternativa atómica sin lock (optimista)

Si la sobrecarga del lock es inaceptable, se podría usar un patrón **CAS (compare-and-swap)** sobre referencias compartidas (p. ej., punteros `queue.head`), pero el GIL de Python y la complejidad de las estructuras sin lock hacen esto poco práctico. Las operaciones de deque son extensiones C y liberan el GIL, por lo que un `threading.Lock` alrededor de `popleft()` es la solución correcta más simple.

### Resumen del orden de mutación para garantizar corrección

| Método | Orden seguro de mutación |
|---|---|
| `enqueue` | 1. Lock → 2. `append(patient)` → 3. Unlock |
| `dequeue` | 1. Lock → 2. Verificar `is_empty` → 3. `popleft()` del primero no vacío → 4. Unlock → 5. Devolver paciente |
| `peek` | 1. Lock → 2. Leer `[0]` del primero no vacío → 3. Unlock → 4. Devolver paciente |
| `list_queue` | 1. Lock → 2. Copiar todos los deques → 3. Unlock → 4. Devolver copia |
| `stats` | 1. Lock → 2. Leer `len()` de cada deque → 3. Unlock → 4. Devolver dict |

La regla de oro: **leer y mutar bajo la misma adquisición del lock**. Nunca leer el estado, liberar el lock y luego mutar basándose en datos obsoletos — así es como ocurre el doble procesamiento.

---

*Última actualización: 2026-10-18*