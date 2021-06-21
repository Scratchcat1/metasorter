[X] Handle files which have identical times
[ ] Fix package needing to install dependencies manually  
[X] Add per day locking
[X] Delete locks after a while
[ ] Fix race condition. If a lock deletion occurs between the return of the lock and its acquiring the thread may end up with a lock not connected to
[X] Arbitrary counter
[X] Handle the creation of files inside of folders
[ ] Delete empty folders later
[ ] Determine if the delayed lock deletion is actually needed. It may be cheaper to delete the lock than create a new thread/timer. Instead it may be sensible to delete if no other processes are currently waiting for the lock via the date counter.
[ ] Requirements:
- watchdog ffmpeg-python