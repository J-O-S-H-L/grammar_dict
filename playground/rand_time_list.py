import random


def gen_random_sleeps(min_sleep, max_total_time, n_requests):
    """
    Generates a list of random sleep intervals for web scraping.

    Parameters:
        min_sleep (float): Minimum sleep interval in seconds.
        max_total_time (float): Maximum total time in seconds for all requests.
        n_requests (int): Number of requests to make (length of sleep intervals list).

    Returns:
        list of float: Random sleep intervals in seconds.
    """
    if n_requests * min_sleep > max_total_time:
        raise ValueError(
            "Minimum sleep times number of requests exceed the maximum total time."
        )

    # Allocate initial min_sleep to each request
    remaining_time = max_total_time - (n_requests * min_sleep)
    sleep_intervals = [min_sleep] * n_requests

    # Distribute the remaining time randomly across the sleep intervals
    for i in range(n_requests):
        if remaining_time <= 0:
            break
        max_additional_sleep = remaining_time / (n_requests - i)
        additional_sleep = random.uniform(0, max_additional_sleep)
        sleep_intervals[i] += additional_sleep
        remaining_time -= additional_sleep

    # Shuffle to randomize the sleep intervals distribution
    random.shuffle(sleep_intervals)

    return sleep_intervals


if __name__ == "__main__":

    min_sleep = 2  # Minimum sleep of 2 seconds
    max_total_time = 100  # Maximum total time of 100 seconds
    n_requests = 10  # Number of requests

    sleep_intervals = gen_random_sleeps(min_sleep, max_total_time, n_requests)
    print(sleep_intervals)
    print(f"Total sleep time: {sum(sleep_intervals)} seconds")
