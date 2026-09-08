import tracemalloc
from time import perf_counter
from functools import wraps
from typing import Callable, Any


def profile_performance(active: bool = True) -> Callable:
    """
        Decorator combining execution time (perf_counter)
        and memory analysis (tracemalloc).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not active:
                return func(*args, **kwargs)

            tracemalloc.start()
            start_time = perf_counter()

            result = func(*args, **kwargs)

            elapsed_time = perf_counter() - start_time
            actual_size, peak_maximal = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print(f"\n[PROFILING REPORT: '{func.__name__}']")
            print(f"  • Execution time : {elapsed_time:.4f} secondes")
            print(f"  • Current memory : {actual_size / 10**6:.2f} MB")
            print(f"  • Memory peak   : {peak_maximal / 10**6:.2f} MB\n")

            return result
        return wrapper
    return decorator