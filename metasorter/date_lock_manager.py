from threading import Lock, Timer
import logging


class DateLockManager:
    """
    Manages access to multiple locks for obtaining exclusive access to a particular date to prevent
    race conditions when resolving collisions between files with the same date.
    """

    def __init__(self):
        self._access_lock = Lock()
        # Maps dates to lock objects
        self._date_locks = {}
        # Keeps track of the number of threads which want access to this lock
        # When it drops to 0 the lock can be deleted to save memory
        self._date_counters = {}
        self._logger = logging.getLogger(__name__)

    def get_date_lock(self, date):
        "Get the lock object for a date or create one if it doesn't exist"
        # Avoid race condition where two locks are created for the same date
        with self._access_lock:
            self._date_counters[date] = self._date_counters.get(date, 0) + 1
            if date in self._date_locks:
                return self._date_locks[date]
            else:
                self._date_locks[date] = Lock()
                return self._date_locks[date]

    def start_delayed_delete_lock(self, date):

        """
        Start a timer to delete a date lock.
        The delay avoids needlessly deleting and recreating the lock if it will be used again
        in the near future.
        """
        with self._access_lock:
            self._date_counters[date] -= 1
        timer = Timer(30, self.delete_lock, args=(date,))
        timer.start()

    def delete_lock(self, date):
        "Delete a lock if it exists and isn't being held by another process"
        with self._access_lock:
            if date in self._date_locks:
                assert (
                    date in self._date_counters
                ), "Date was not found in date_counters even though date is in date_locks"
                if self._date_counters[date] == 0:
                    self._date_counters.pop(date)
                    self._date_locks.pop(date)
                    self._logger.debug("Removed date lock for date %s", date)
