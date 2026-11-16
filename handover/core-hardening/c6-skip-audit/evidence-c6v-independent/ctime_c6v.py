"""c6v: the two example answer times of the start box, derived from the check time (they must be later than the check time).
example_times(check_time_utc 'YYYY-MM-DDTHH:MM:SSZ') -> (ex1_utc, ex1_ist, ex2_utc, ex2_ist) as printed in the box: 'UTC = IST date-time' pairs."""
import datetime
def example_times(ct):
    t = datetime.datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(minutes=15)
    t = t.replace(second=0, microsecond=0) + datetime.timedelta(minutes=(10 - t.minute % 10) % 10 or 0)
    if t < datetime.datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(minutes=15):
        t += datetime.timedelta(minutes=10)
    t2 = t + datetime.timedelta(minutes=10)
    f = lambda x: x.strftime("%Y-%m-%dT%H:%M:%SZ")
    g = lambda x: (x + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
    return f(t), g(t), f(t2), g(t2)
