from ..constants import (
    SELECTIVE_REPEAT,
    SELECTIVE_REPEAT_PROTOCOL,
    STOP_AND_WAIT,
    STOP_AND_WAIT_PROTOCOL,
)
from .stop_and_wait import StopAndWait


def protocol_id_from_choice(protocol_choice):
    if isinstance(protocol_choice, int):
        return protocol_choice
    if protocol_choice == STOP_AND_WAIT:
        return STOP_AND_WAIT_PROTOCOL
    if protocol_choice == SELECTIVE_REPEAT:
        return SELECTIVE_REPEAT_PROTOCOL
    raise ValueError(f"Protocolo desconocido: {protocol_choice}")


def create_protocol(protocol_id, op_type, sock, **kwargs):
    if protocol_id == STOP_AND_WAIT_PROTOCOL:
        return StopAndWait(op_type, sock, **kwargs)
    if protocol_id == SELECTIVE_REPEAT_PROTOCOL:
        raise NotImplementedError("Selective Repeat aun no esta implementado.")
    raise ValueError(f"ID de protocolo desconocido: {protocol_id}")
