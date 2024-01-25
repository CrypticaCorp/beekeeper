# BeeKeeper - GFS Backup Retention Script

BeeKeeper efficiently manages and deletes backups, adhering to a configurable Grandfather-Father-Son (GFS) retention policy.
It offers precise control over backup retention periods across different levels (daily, weekly, monthly, yearly), providing a
robust solution for optimizing disk space and maintaining essential backups.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Usage](#usage)
  - [Options](#options)
  - [Examples](#examples)
- [Notes](#notes)
- [License](#license)
- [Copyright](#copyright)

## Features

- **Flexible Backup Retention**: Configure daily, weekly, monthly, and yearly retention periods through command-line arguments.
- **Dry Run Option**: Simulate file deletion to review what files would be deleted before actually performing the operation.
- **Recursive Directory Traversal**: Optionally traverse directories recursively to manage backups in nested folders.
- **Empty Folder Cleanup**: Clean up empty directories after backup files have been deleted.

## Requirements

- Python 3.6 or higher.
- Proper permissions to access and modify the files and directories you wish to manage.

## Usage

Run the script from the command line, providing the necessary arguments to configure the backup retention policy and other options.

```bash
./beekeeper.py <path_to_files> [options]
```

### Options

- `--max-age-daily`: Maximum age for daily backups (default: 30)
- `--max-age-weekly`: Maximum age for weekly backups (default: 365)
- `--max-age-monthly`: Maximum age for monthly backups (default: 1095)
- `--max-age-yearly`: Maximum age for yearly backups (default: 3*365)
- `--dry-run`: Dry run (does not delete files)
- `--use-filename`: Use filename to determine file age
- `--recursive`: Recursively search directories for files to delete
- `--clean-folders`: Remove empty folders after file deletion (requires `--recursive`)
- `--follow-symlinks`: Follow symbolic links (default: do not follow)
- `--log-level`: Set the logging level (options: DEBUG, INFO, WARNING, ERROR, CRITICAL; default: INFO)

### Examples

1. **Standard Retention Policy:**
   Configure the script to:
   - Preserve all backups from the last 30 days.
   - For backups that are 31 days to 1 year old, preserve the most recent file per week.
   - For backups that are 1 year to 3 years old, preserve the most recent file per year.
   - Automatically discard backups older than 3 years.

   Run the script with the following options:

   ```bash
   ./beekeeper.py /path/to/your/backups --max-age-daily 30 --max-age-weekly 365 --max-age-monthly 1095 --max-age-yearly 1095
   ```

2. **Short-term Backup Retention:**
   - Preserves daily backups for the last 7 days.
   - Preserves weekly backups for backups older than 7 days up to 30 days.
   - Preserves monthly backups for backups older than 30 days up to 180 days.
   - Discards backups older than 180 days.

   ```bash
   ./beekeeper.py /path/to/your/backups --max-age-daily 7 --max-age-weekly 30 --max-age-monthly 180 --max-age-yearly 180
   ```

3. **Long-term Backup Retention:**
   - Preserves daily backups for the last 60 days.
   - Preserves weekly backups for backups older than 60 days up to 1 year.
   - Preserves monthly backups for backups older than 1 year up to 5 years.
   - Discards backups older than 5 years.

   ```bash
   ./beekeeper.py /path/to/your/backups --max-age-daily 60 --max-age-weekly 365 --max-age-monthly 1825 --max-age-yearly 1825
   ```

## Notes

- **Logging**: All operations are logged to the `beekeeper.log` file. This file contains information about the script's operations, including files deleted and potential errors encountered.

## License

This script is published under the Apache License 2.0. Please see the `LICENSE` file for more details.

## Copyright

© 2024 Cryptica AB. All rights reserved.

For more information about Cryptica AB, please visit [https://cryptica.se](https://cryptica.se).
