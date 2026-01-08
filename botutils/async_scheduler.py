# async_scheduler.py
from botutils.event_loop import loop
#from ui_logger import kivy_print

def schedule_coroutine(coro_func, *args, label="task", **kwargs):
    """
    Safely schedule any coroutine on the global event loop.
    
    - coro_func: The coroutine function (not awaited)
    - *args/**kwargs: Arguments to pass to the coroutine
    - label: Optional label for debug/logging
    """
    import threading
    print(f"🧠 Called from loop id: {id(loop)} | Thread: {threading.current_thread().name}")
    def safe_schedule():
        try:
            task = loop.create_task(coro_func(*args, **kwargs))

            def done_callback(fut):
                try:
                    result = fut.result()
                    print(f"✅ {label} result: {result}")
                except Exception as e:
                    print(f"❌ Exception in {label}: {e}")

            task.add_done_callback(done_callback)

        except Exception as e:
            print(f"❌ Failed to schedule {label}: {e}")

    loop.call_soon_threadsafe(safe_schedule)