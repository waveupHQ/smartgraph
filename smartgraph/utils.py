# smartgraph/utils.py

import asyncio
from typing import Any

from reactivex import Observable


async def process_observable(observable: Observable) -> Any:
    future = asyncio.Future()

    def on_next(value):
        if not future.done():
            future.set_result(value)

    def on_error(error):
        if not future.done():
            future.set_exception(error)

    def on_completed():
        if not future.done():
            future.set_result(None)

    observable.subscribe(on_next, on_error, on_completed)

    return await future


# This code defines an asynchronous function called `process_observable` that takes an Observable as input.
# It creates an asyncio Future object to handle the asynchronous operation.
# The function sets up three callback functions: on_next, on_error, and on_completed.
# These callbacks are used to handle different events from the Observable:
# - on_next: Sets the Future's result to the received value if the Future is not already done.
# - on_error: Sets an exception on the Future if an error occurs and the Future is not already done.
# - on_completed: Sets the Future's result to None if the Observable completes and the Future is not already done.
# The Observable is then subscribed to using these callback functions.
# Finally, the function awaits and returns the Future's result, effectively converting the Observable to an awaitable.
# This allows asynchronous processing of the Observable's events in an asyncio-compatible way.
