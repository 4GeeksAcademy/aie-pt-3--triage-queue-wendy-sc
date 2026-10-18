# CONTEXT --- Triage Queue — Gestor de Cola de Prioridad

El departamento de informática de un hospital público ha recibido el encargo de modernizar el proceso de triaje en su unidad de urgencias. Actualmente, una enfermera apunta manualmente los nombres de los pacientes en una pizarra y los llama por orden de llegada. Esto genera caos cuando llega un caso crítico y hay que saltarse la cola, o cuando dos personas intentan actualizar la pizarra al mismo tiempo y se borra una entrada.

El responsable técnico del hospital te ha entregado una especificación con lo que debe hacer el nuevo gestor de colas de triaje. El sistema correrá en terminal por ahora — sin interfaz gráfica, solo un programa limpio en Python que modele y opere la cola correctamente, listo para integrarse más adelante en una aplicación mayor.

## Ticket recibido

La especificación del responsable técnico dice lo siguiente:

### Entrada de pacientes
- Cuando llega un nuevo paciente, se le asigna un nivel de triaje (1 = crítico, 2 = urgente, 3 = estándar).
- Se deben registrar el nombre del paciente, el momento de llegada y el nivel de triaje.

### Orden de atención
- Los pacientes con nivel 1 siempre se atienden antes que los de nivel 2, y estos antes que los de nivel 3.
- Dentro del mismo nivel de triaje, los pacientes se atienden en orden de llegada (FIFO).

### Operaciones requeridas
- Encolar: añadir un nuevo paciente.
- Desencolar: llamar al siguiente paciente para ser atendido.
- Peek: mostrar quién es el siguiente sin retirarlo de la cola.
- Listar cola: mostrar todos los pacientes en espera, en el orden en que serán atendidos.
- Stats: reportar el número de pacientes en espera por nivel de triaje.

## Objetivo

Una `deque` simple no será suficiente aquí — tendrás que pensar con cuidado cómo modelar una cola de prioridad y qué estructura de datos soporta mejor las operaciones requeridas. Piensa en qué ocurre si llega un paciente de nivel 1 mientras la cola se está procesando: ¿cómo garantizas que se coloca correctamente sin reordenar toda la cola en cada inserción?