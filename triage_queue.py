#!/usr/bin/env python3
"""
Triage Queue — Priority-based patient queue for hospital emergency triage.

Patients are attended by triage level (1 = critical first) and within the same
level by order of arrival (FIFO). Uses three separate deques, one per triage level.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import sys


# ── Data Model ──────────────────────────────────────────────────────────────

@dataclass(order=True)
class Patient:
    """Represents a patient in the triage queue.

    Attributes:
        name:        Full name of the patient.
        triage_level: Severity level (1 = critical, 2 = urgent, 3 = standard).
        arrived_at:  Timestamp when the patient was registered.
    """
    name: str = field(compare=False)
    triage_level: int = field(compare=False)
    arrived_at: datetime = field(compare=False)


# ── Triage Queue ────────────────────────────────────────────────────────────

class TriageQueue:
    """A priority queue for triage patients backed by three internal deques.

    Level 1 (critical) patients are always attended before level 2 (urgent),
    which are attended before level 3 (standard). Within the same level,
    patients are attended in strict FIFO order.

    Design rationale
    ----------------
    Three separate ``collections.deque`` instances (one per triage level) give
    O(1) enqueue / dequeue / peek, O(1) stats, and natural FIFO ordering
    without re-sorting.  See DESIGN.md for a full comparison with alternatives.
    """

    def __init__(self) -> None:
        self._queues: dict[int, deque[Patient]] = {
            1: deque(),
            2: deque(),
            3: deque(),
        }

    # ── Public API ───────────────────────────────────────────────────────

    def enqueue(self, patient: Patient) -> None:
        """Add *patient* to the queue at their triage level.

        Raises:
            ValueError: If ``triage_level`` is not 1, 2 or 3.
        """
        if patient.triage_level not in (1, 2, 3):
            raise ValueError(
                f"Invalid triage level: {patient.triage_level}. "
                f"Must be 1 (critical), 2 (urgent), or 3 (standard)."
            )
        self._queues[patient.triage_level].append(patient)

    def dequeue(self) -> Patient:
        """Remove and return the next patient to be attended.

        Returns:
            The highest-priority patient (lowest triage level, earliest
            arrival within that level).

        Raises:
            IndexError: If the queue is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot dequeue from an empty triage queue.")
        for level in (1, 2, 3):
            if self._queues[level]:
                return self._queues[level].popleft()
        # Defensive — should never reach here because of the is_empty() guard.
        raise IndexError("Cannot dequeue from an empty triage queue.")

    def peek(self) -> Patient | None:
        """Return the next patient without removing them, or ``None`` if empty."""
        for level in (1, 2, 3):
            if self._queues[level]:
                return self._queues[level][0]
        return None

    def list_queue(self) -> list[Patient]:
        """Return all waiting patients in attendance order as a fresh list."""
        result: list[Patient] = []
        for level in (1, 2, 3):
            result.extend(self._queues[level])
        return result

    def stats(self) -> dict[str, int]:
        """Return a dict with the number of waiting patients per triage level."""
        return {
            "critical": len(self._queues[1]),
            "urgent":    len(self._queues[2]),
            "standard":  len(self._queues[3]),
        }

    # ── Helpers ──────────────────────────────────────────────────────────

    def is_empty(self) -> bool:
        """Return ``True`` if there are no patients waiting."""
        return all(len(q) == 0 for q in self._queues.values())

    def __len__(self) -> int:
        return sum(len(q) for q in self._queues.values())


# ── CLI helpers ─────────────────────────────────────────────────────────────

def _get_int_input(prompt: str, min_val: int, max_val: int) -> int:
    """Prompt the user for an integer within [min_val, max_val].

    Loops until a valid integer is entered.  Exits gracefully on EOF / Ctrl+C.
    """
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            print(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)


def _add_patient(queue: TriageQueue) -> None:
    """Prompt for patient details and enqueue."""
    print("\n--- Add New Patient ---")
    name = input("Patient name: ").strip()
    if not name:
        print("Patient name cannot be empty.")
        return
    print("Triage levels: 1 = Critical  2 = Urgent  3 = Standard")
    level = _get_int_input("Triage level [1-3]: ", 1, 3)
    patient = Patient(name=name, triage_level=level, arrived_at=datetime.now())
    queue.enqueue(patient)
    print(
        f"Patient '{patient.name}' (level {patient.triage_level}) "
        f"added to the queue."
    )


def _call_next(queue: TriageQueue) -> None:
    """Dequeue and display the next patient."""
    try:
        patient = queue.dequeue()
    except IndexError as exc:
        print(f"\n{exc}")
        return
    print(
        f"\nNext patient to attend: {patient.name} "
        f"(Level {patient.triage_level}, "
        f"arrived at {patient.arrived_at.strftime('%H:%M:%S')})"
    )


def _view_queue(queue: TriageQueue) -> None:
    """Display all patients in attendance order."""
    patients = queue.list_queue()
    if not patients:
        print("\nThe queue is empty.")
        return
    print(f"\n--- Current Queue ({len(patients)} patients) ---")
    print(f"{'#':<4} {'Name':<20} {'Level':<8} {'Arrived':<12}")
    print("-" * 50)
    for i, p in enumerate(patients, 1):
        print(
            f"{i:<4} {p.name:<20} {p.triage_level:<8} "
            f"{p.arrived_at.strftime('%H:%M:%S'):<12}"
        )


def _view_stats(queue: TriageQueue) -> None:
    """Display queue statistics by triage level."""
    stats = queue.stats()
    total = sum(stats.values())
    print(f"\n--- Queue Statistics ---")
    print(f"  Critical (level 1): {stats['critical']} patient(s)")
    print(f"  Urgent   (level 2): {stats['urgent']} patient(s)")
    print(f"  Standard (level 3): {stats['standard']} patient(s)")
    print(f"  Total waiting:      {total} patient(s)")
    if next_patient := queue.peek():
        print(f"  Next to attend:     {next_patient.name}")


# ── Main loop ───────────────────────────────────────────────────────────────

def _main_loop() -> None:
    """Run the interactive CLI menu for the triage queue."""
    queue = TriageQueue()

    # Map option key -> (description, handler)
    menu: dict[str, tuple[str, callable]] = {
        "1": ("Add a new patient",       _add_patient),
        "2": ("Call next patient",       _call_next),
        "3": ("View current queue",      _view_queue),
        "4": ("View queue statistics",   _view_stats),
        "5": ("Exit",                    lambda q: sys.exit(0)),
    }

    while True:
        print("\n" + "=" * 44)
        print("   HOSPITAL TRIAGE QUEUE SYSTEM")
        print("=" * 44)
        for key, (desc, _) in menu.items():
            print(f"  {key}. {desc}")
        print("=" * 44)

        choice = _get_int_input("Select an option [1-5]: ", 1, 5)
        key = str(choice)
        handler = menu[key][1]
        try:
            handler(queue)
        except Exception as exc:
            print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    _main_loop()