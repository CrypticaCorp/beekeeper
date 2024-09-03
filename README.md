# BeeKeeper - GFS Backup Retention Script

BeeKeeper efficiently manages and deletes backups, adhering to a configurable Grandfather-Father-Son (GFS) retention policy.
It offers precise control over backup retention periods across different levels (daily, weekly, monthly, yearly), providing a
robust solution for optimizing disk space and maintaining essential backups.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Options](#options)
  - [Examples](#examples)
- [Notes](#notes)
- [License](#license)
- [Copyright](#copyright)

## Features
- **Selective Retention Policies**: Configure retention periods for daily, weekly, monthly, and yearly backups.
- **Dry Run Mode**: Preview the files that would be deleted without making any changes to the system.
- **Filename Date Extraction**: Extract dates from filenames using customizable patterns for more accurate file management.
- **Robust Logging**: Comprehensive logging for monitoring script actions and debugging issues.
- **Error Handling**: Gracefully handle and log errors for uninterrupted execution.
- **Force Mode**: Skip confirmation before deleting backups for automated scenarios.
- **Path Validation**: Ensure the provided filepath exists and is accessible before processing.

## Requirements
- Python 3.6 or higher
- No external dependencies required.

## Installation
Clone the repository or download the script directly. Ensure that Python 3 is installed on your system.

```bash
git clone https://github.com/CrypticaCorp/beekeeper.git
cd beekeeper
chmod +x beekeeper.py
```

## Usage
Run the script from the command line, providing the necessary arguments to configure the backup retention policy and other options.

```bash
./beekeeper.py <path_to_files> [options]
```

### Options
The script supports various command-line options for customizing its behavior:

- `filepath`: Path to the files or directories to manage.
- `--dry-run`: Execute the script in dry run mode. No files will be deleted.
- `--use-filename`: Use the date from the filename to determine the age of the file, instead of the file modification time.
- `--max-age-daily DAYS`: Set the maximum age in days for daily backups. Default is 30 days.
- `--max-age-weekly DAYS`: Set the maximum age in days for weekly backups. Default is 365 days.
- `--max-age-monthly DAYS`: Set the maximum age in days for monthly backups. Default is 1095 days.
- `--max-age-yearly DAYS`: Set the maximum age in days for yearly backups. Default is 3*365 days.
- `--log-level LEVEL`: Set the logging level. Options are 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Default is 'INFO'.
- `--log-file FILE`: Specify the path to the log file. Default is 'beekeeper.log'.
- `--force`: Skip confirmation before deleting backups. Use with caution.

### Examples
1. **Standard Retention Policy:**
   Configure the script to:
   - Preserve all backups from the last 30 days.
   - For backups that are 31 days to 1 year old, preserve the most recent file per week.
   - For backups that are 1 year to 3 years old, preserve the most recent file per month.
   - Automatically discard backups older than 3 years.

   Run the script with the following options:

   ```bash
   ./beekeeper.py /path/to/your/backups --max-age-daily 30 --max-age-weekly 365 --max-age-monthly 1095 --max-age-yearly 1095
   ```

2. **Short-term Backup Retention with Force Mode:**
   - Preserves daily backups for the last 7 days.
   - Preserves weekly backups for backups older than 7 days up to 30 days.
   - Preserves monthly backups for backups older than 30 days up to 180 days.
   - Discards backups older than 180 days.
   - Skips confirmation before deleting.

   ```bash
   ./beekeeper.py /path/to/your/backups --max-age-daily 7 --max-age-weekly 30 --max-age-monthly 180 --max-age-yearly 180 --force
   ```

3. **Long-term Backup Retention with Custom Log File:**
   - Preserves daily backups for the last 60 days.
   - Preserves weekly backups for backups older than 60 days up to 1 year.
   - Preserves monthly backups for backups older than 1 year up to 5 years.
   - Discards backups older than 5 years.
   - Uses a custom log file.

   ```bash
   ./beekeeper.py /path/to/your/backups --max-age-daily 60 --max-age-weekly 365 --max-age-monthly 1825 --max-age-yearly 1825 --log-file /path/to/custom_log.log
   ```

## Notes
- **File or directory age**: File or directory age is determined by last modification time unless `--use-filename` is specified.
- **Logging**: All operations are logged to the specified log file (default: `beekeeper.log`). This file contains information about the script's operations, including files deleted and potential errors encountered.
- **Determining file age based on filename**: When the `--use-filename` option is used, the script determines the age of a file or directory based on a date found in its name instead of last modification time. Following date formats are supported: `YYYY-MM-DD`, `YYYY_MM_DD`, `YYYYMMDD`, `YYYY-MM-DD_HH-MM`, `YYYY_MM_DD_HH_MM` and `YYYYMMDD_HHMM`
- **Path Validation**: The script checks if the specified path exists, is a directory, and is readable before processing.
- **Force Mode**: Use the `--force` option with caution, as it skips the confirmation step before deleting backups.

## License
This script is published under the Apache License 2.0. Please see the `LICENSE` file for more details.

## Copyright
© 2024 Cryptica AB. All rights reserved.
For more information about Cryptica AB, please visit [https://cryptica.se](https://cryptica.se).