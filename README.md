# MetaSorter
MetaSorter is a tool to automatically rename and organise photos and videos by date.

## Features
- Rename and sort photos and videos based on date taken.
- Deduplicate identical media.
- Watch folders to automatically sort incoming media.
- Include/exclude files with regular expressions.

## Installation
Install dependencies with pip
```
$ python3 -m pip install --upgrade pip
$ pip install -r requirements.txt
```

## Configuration
```
// metasorter.json
{
    // Message level to log. One of ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    "logging_level": "INFO",

    // Filepath to logfile
    "logfile": "testing/metasorter.log",


    "media_types": {
        "photo": [
            "jpg",
            "jpeg",
            "JPG",
            "JPEG",
            "png",
            "PNG",
            "HEIC",
            "heic"
        ],
        "video": [
            "mp4",
            "MP4",
            "mov",
            "MOV"
        ]
    },
    
    // List of folder watch configurations
    "folders": [
        {
            // Source directory which will be watched for new media files.
            "source": "testing/input",
            // Destination directory where the media will be copied to.
            "destination": "testing/output",

            // The minimum time to wait in seconds to wait after the file copy starts before file size polling begins.
            "max_transfer_time": 1,

            // Include/Exclude regular expressions. A file is accepted if any include expressions match and no exclude expressions match.
            "patterns": {
                "include": [
                    ".*"
                ],
                "exclude": []
            },

            // Flag if the file should be deleted from the source directory after being copied.
            "remove": true
        }
    ]
}
```