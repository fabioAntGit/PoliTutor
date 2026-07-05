import asyncio

_background_tasks: set[asyncio.Task] = set()

def run_in_background(coro) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
