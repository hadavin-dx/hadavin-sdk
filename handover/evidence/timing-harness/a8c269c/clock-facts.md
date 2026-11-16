```
start load 3.70 7.32 8.99 5/209 23069
namespace(implementation='clock_gettime(CLOCK_PROCESS_CPUTIME_ID)', monotonic=True, adjustable=False, resolution=1e-09)
namespace(implementation='clock_gettime(CLOCK_MONOTONIC)', monotonic=True, adjustable=False, resolution=1e-09)
rc=0
3.13.18 (main, Oct 26 2026, 14:08:19) [Clang 23.1.3 ]
linux
namespace(implementation='clock_gettime(CLOCK_PROCESS_CPUTIME_ID)', monotonic=True, adjustable=False, resolution=1e-09)
namespace(implementation='clock_gettime(CLOCK_MONOTONIC)', monotonic=True, adjustable=False, resolution=1e-09)
A baseline: empty loop only: wall=0.0000s process_time=0.0000s thread_time(this thread)=0.0000s
B main thread sleeps 1.0 s, nothing else: wall=1.0002s process_time=0.0001s thread_time(this thread)=0.0001s
C busy thread beside; main thread sleeps 1.0 s then empty loop: wall=1.0120s process_time=0.7021s thread_time(this thread)=0.0001s
D subprocess burning 1.0 s CPU, started and waited for (reaped) inside the timed section: wall=1.1834s process_time=0.0003s thread_time(this thread)=0.0003s
os.times() after D (user, system, children_user, children_system, elapsed): posix.times_result(user=0.72, system=0.0, children_user=0.46, children_system=0.55, elapsed=17189196.6)
rc=0 end load 3.70 7.32 8.99 5/210 23156
```
