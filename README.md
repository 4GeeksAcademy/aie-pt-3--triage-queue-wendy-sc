# Triage Queue — Priority Queue Manager

Gestor de cola de prioridad para triaje hospitalario. Implementación en Python con interfaz CLI que modela pacientes, respeta niveles de urgencia (1 crítico → 2 urgente → 3 estándar) y mantiene orden FIFO dentro del mismo nivel.

---

## 📋 Requisitos

- **Python 3.11+** (usa `typing` con `|` para uniones de tipos)
- Solo usa la **biblioteca estándar** (`collections.deque`, `dataclasses`, `datetime`). Sin paquetes externos.

---

## 🚀 Uso

```bash
python3 triage_queue.py
```

Se abre un menú interactivo en la terminal:

```
============================================
   HOSPITAL TRIAGE QUEUE SYSTEM
============================================
  1. Add a new patient
  2. Call next patient
  3. View current queue
  4. View queue statistics
  5. Exit
============================================
Select an option [1-5]:
```

### Opciones

| Opción | Descripción |
|---|---|
| **1** | Añadir paciente: solicita nombre y nivel de triaje (1=crítico, 2=urgente, 3=estándar). |
| **2** | Llamar al siguiente paciente: desencola y muestra quién debe ser atendido. |
| **3** | Ver cola actual: muestra todos los pacientes en espera en orden de atención. |
| **4** | Ver estadísticas: cuenta de pacientes por nivel de triaje. |
| **5** | Salir del programa. |

---

## 📁 Archivos del proyecto

| Archivo | Propósito |
|---|---|
| `triage_queue.py` | Punto de entrada. Contiene `Patient` (dataclass), `TriageQueue` (cola de prioridad) y el bucle CLI. |
| `DESIGN.md` | Documento de diseño: justificación de la estructura de datos y análisis de concurrencia. |
| `README.md` | Este archivo. |

---

## 🧠 Diseño

La cola interna usa **tres `collections.deque` separados**, uno por nivel de triaje:

```python
self._queues = {
    1: deque(),   # Crítico
    2: deque(),   # Urgente
    3: deque(),   # Estándar
}
```

- `enqueue()` → O(1) — añade al deque del nivel correspondiente.
- `dequeue()` → O(1) — recorre niveles 1→2→3 y extrae del primero no vacío.
- `peek()` → O(1) — inspecciona el frente sin extraer.
- `list_queue()` → O(n) — concatena los tres deques en orden.
- `stats()` → O(1) — tres llamadas a `len()`.

Consulta [`DESIGN.md`](./DESIGN.md) para una comparación detallada con alternativas (heapq, deque ordenado, listas) y el análisis de condiciones de carrera en escenarios concurrentes.

---

## ✅ Pruebas

Ejecuta todas las verificaciones con:

```bash
python3 -c "
from triage_queue import Patient, TriageQueue
from datetime import datetime
import time

# Test de orden de prioridad
q = TriageQueue()
for p in [Patient('Std',3,datetime.now()), Patient('Urg',2,datetime.now()), Patient('Crit',1,datetime.now())]:
    q.enqueue(p)
assert q.dequeue().name == 'Crit'
assert q.dequeue().name == 'Urg'
assert q.dequeue().name == 'Std'
print('✓ Prioridad 1 > 2 > 3')

# Test FIFO mismo nivel
q2 = TriageQueue()
a, b, c = Patient('A',2,datetime.now()), Patient('B',2,datetime.now()), Patient('C',2,datetime.now())
q2.enqueue(a); q2.enqueue(b); q2.enqueue(c)
assert q2.dequeue() is a and q2.dequeue() is b and q2.dequeue() is c
print('✓ FIFO mismo nivel')

# Test cola vacía
q3 = TriageQueue()
assert q3.peek() is None
try:
    q3.dequeue()
    assert False
except IndexError:
    print('✓ Empty queue handling')

print()
print('Todos los tests pasaron.')
"
```

---

## 📄 Licencia

Proyecto educativo de [4Geeks Academy](https://4geeksacademy.com/).
