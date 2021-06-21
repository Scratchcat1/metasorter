#!/usr/bin/python3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import re
import datetime
import shutil
import stat
import ffmpeg
import exifread
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
import json
import getopt
import sys
from metasorter.date_lock_manager import DateLockManager

logger = logging.getLogger(__name__)
date_lock_manager = DateLockManager()


class PatternChecker:
    def __init__(self, includes, excludes):
        self._include_regexps = self.create_regexps(includes)
        self._exclude_regexps = self.create_regexps(excludes)

    @staticmethod
    def create_regexps(patterns):
        regexps = []
        for pattern in patterns:
            regexps.append(re.compile(pattern))
        return regexps

    def check(self, string):
        return any(
            [regexp.match(string) for regexp in self._include_regexps]
        ) and not any([regexp.match(string) for regexp in self._exclude_regexps])


class FileWatchHandler(FileSystemEventHandler):
    def __init__(self, folder_details, config, t_executor):
        FileSystemEventHandler.__init__(self)
        self._folder_details = folder_details
        self._config = config
        self._executor = t_executor
        self._pattern_checker = PatternChecker(
            folder_details["patterns"]["include"], folder_details["patterns"]["exclude"]
        )

    def on_created(self, event):  # when file is created
        """
        Add the event to the queue to be processed by the threadpool
        """
        logger.debug("Got event for file %s", event.src_path)
        if not event.is_directory and self._pattern_checker.check(event.src_path):
            self._executor.submit(
                on_created_file_handler,
                event,
                self._pattern_checker,
                self._config,
                self._folder_details,
            )


def wait_until_constant_file_size(path, check_period):
    """
    Waits until the file size stops changing for check_period time
    If the file does keep changing size send warnings that the
    transfer is taking longer than expected
    """
    previous_size = os.path.getsize(path)
    while True:
        time.sleep(check_period)
        current_size = os.path.getsize(path)
        if current_size == previous_size:
            break
        previous_size = current_size
        logger.warning(
            "File %s is taking longer than expected to transfer, current size: %s",
            path,
            current_size,
        )


def on_created_file_handler(event, pattern_checker, config, folder_details):
    try:
        # Wait for the transfer to complete
        logger.debug("Accepted event for file %s", event.src_path)
        time.sleep(folder_details["max_transfer_time"])
        wait_until_constant_file_size(event.src_path, 5)

        if os.path.getsize(event.src_path) == 0:
            raise Exception("Empty file")

        date_taken = None
        # Split off the extension (e.g. ".ext"), remove the leading dot
        ext = os.path.splitext(event.src_path)[1][1:].lower()
        if ext in config["media_types"]["photo"]:
            date_taken = photo_date_taken(event)
        elif ext in config["media_types"]["video"]:
            date_taken = video_date_taken(event)
        else:
            # The extension is not one we know of. Warn that this has occurred.
            logger.warning("No media type match found for file %s", event.src_path)
            return None

        if date_taken:
            dest_folder = os.path.join(
                folder_details["destination"],
                str(date_taken.year),
                str(date_taken.month).zfill(2),
            )
            date_string = date_taken.strftime("%Y-%m-%dT%H-%M-%S")
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder, exist_ok=True)

            # Prevent a race condition occurring when two files resolve collisions at the same time
            with date_lock_manager.get_date_lock(date_string):
                new_filename = (
                    date_string
                    + "_"
                    + resolve_collision(event.src_path, dest_folder, date_string, ext)
                    + "."
                    + ext
                )

                dest_filepath = os.path.join(dest_folder, new_filename)
                shutil.copyfile(event.src_path, dest_filepath)
                logger.info("Copied file %s to %s", event.src_path, dest_filepath)
                os.chmod(
                    dest_filepath,
                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP,
                )

                if folder_details["remove"]:
                    os.remove(event.src_path)
                    logger.info("Removed file %s", event.src_path)

            # Notify the lock manager that a thread has completed its use of the lock
            date_lock_manager.start_delayed_delete_lock(date_string)
        else:
            logger.warning("Date taken not found for file %s", event.src_path)
    except Exception as err:
        logger.exception(
            "Handler failed for file %s. Exception %s", event.src_path, err
        )


def video_date_taken(event):
    probe_results = ffmpeg.probe(event.src_path)
    if "creation_time" in probe_results["format"]["tags"]:
        return datetime.datetime.strptime(
            probe_results["format"]["tags"]["creation_time"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    else:
        return datetime.datetime(1970, 1, 1)


def photo_date_taken(event):
    with open(event.src_path, "rb") as image_fh:
        exif = exifread.process_file(image_fh, details=False)
        if "EXIF DateTimeOriginal" in exif:
            return datetime.datetime.strptime(
                str(exif["EXIF DateTimeOriginal"]), "%Y:%m:%d %H:%M:%S"
            )
        else:
            logger.warning(
                "Unable to extract tag 'EXIF DateTimeOriginal' "
                "from %s. EXIF tags availible are: %s",
                event.src_path,
                str(exif),
            )
            return datetime.datetime(1970, 1, 1)


def hash_file(filepath):
    blocksize = 2 ** 20
    hasher = hashlib.sha256()
    with open(filepath, "rb") as fd:
        buf = fd.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fd.read(blocksize)
    return hasher.hexdigest()


def resolve_collision(src_path, dest_folder, date_string, ext):
    max_counter = -1
    filename_pattern = date_string + "_" + r"(\d+)" + "." + ext
    src_hash = hash_file(src_path)
    if os.path.exists(dest_folder):
        for file in os.listdir(dest_folder):
            match = re.match(filename_pattern, file)
            if match:
                if hash_file(os.path.join(dest_folder, file)) == src_hash:
                    logger.debug(
                        "Found matching hash %s for source file %s at location %s",
                        src_hash,
                        src_path,
                        file,
                    )
                    return match.group(1)
                else:
                    max_counter = max(int(match.group(1)), max_counter)
    return str(max_counter + 1)


def setup_loggers(config):
    logFormatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

    fileHandler = logging.FileHandler(config["logfile"])
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logger.setLevel(level=logging.getLevelName(config["logging_level"]))


def main():
    try:
        opts, _args = getopt.getopt(sys.argv[1:], "c:", ["config="])
    except getopt.GetoptError:
        print("metasorter.py -c <configfile> --config <configfile>")
        sys.exit(2)

    config_file = "resources/metasorter.json"
    for opt, arg in opts:
        if opt == "-h":
            print("metasorter.py -c <configfile> --config <configfile>")
            sys.exit()
        elif opt in ("-c", "--config"):
            config_file = arg

    with open(config_file) as fd:
        config = json.load(fd)

    setup_loggers(config)

    with ThreadPoolExecutor(max_workers=4) as executor:
        logger.debug("Starting file watchers")
        observers = []
        for folder in config["folders"]:
            observer = Observer()
            # create event handler
            event_handler = FileWatchHandler(folder, config, executor)
            # set observer to use created handler in directory.
            # Recursion picks up photos inside of folders
            observer.schedule(event_handler, path=folder["source"], recursive=True)
            observer.start()
            logger.debug("Starting file watcher for folder %s", folder["source"])
            observers.append(observer)
        logger.debug("Started file watchers")

        # sleep until keyboard interrupt, then stop + rejoin the observer
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt. Stopping")
            for observer in observers:
                observer.stop()

        for observer in observers:
            observer.join()


if __name__ == "__main__":
    main()
