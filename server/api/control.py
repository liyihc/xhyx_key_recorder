from fastapi import APIRouter
import keyboard
from ..utils.record import record
api = APIRouter(tags=['control'])

remove_handler = None


@api.get("/api/start")
async def start_hook():
    global remove_handler
    ret = "none"
    if remove_handler is None:
        remove_handler = keyboard.hook(record)
        ret = "added"
    return ret


@api.get("/api/stop")
async def stop_hook():
    global remove_handler
    if remove_handler is not None:
        remove_handler()
        remove_handler = None
