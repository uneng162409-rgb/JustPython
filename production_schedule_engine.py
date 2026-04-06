import random
from datetime import datetime, timedelta

MIN_POST = 3
MAX_POST = 7
MIN_GAP_MINUTES = 50

TIME_WINDOWS = [
    ("06:30", "09:00"),
    ("11:00", "14:00"),
    ("17:00", "21:00")
]


def random_time_in_window(start_str, end_str):
    today = datetime.now().strftime("%Y-%m-%d")
    start = datetime.strptime(today + " " + start_str, "%Y-%m-%d %H:%M")
    end = datetime.strptime(today + " " + end_str, "%Y-%m-%d %H:%M")
    delta = int((end - start).total_seconds())
    random_sec = random.randint(0, delta)
    return start + timedelta(seconds=random_sec)


def generate_schedule():
    target = random.randint(MIN_POST, MAX_POST)
    schedule = []

    while len(schedule) < target:
        window = random.choice(TIME_WINDOWS)
        post_time = random_time_in_window(window[0], window[1])

        if all(abs((post_time - s).total_seconds()) > MIN_GAP_MINUTES * 60 for s in schedule):
            schedule.append(post_time)

    schedule.sort()
    return target, [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in schedule]