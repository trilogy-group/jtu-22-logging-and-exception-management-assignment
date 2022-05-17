import time


def measure_time(func, *args):
    """
    Returns the time taken by the passed lambda function to execute in milliseconds
    along with the result returned by the lambda.
    """
    start_time = time.time()
    result = func(*args)
    time_taken = time.time() - start_time
    return int(time_taken * 1000), result
