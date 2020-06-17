from asyncio import new_event_loop

loop = new_event_loop()


def async_call(func):
    global loop

    def decorator(*args, **kwargs):
        loop.run_until_complete(func(*args, **kwargs))

    return decorator
