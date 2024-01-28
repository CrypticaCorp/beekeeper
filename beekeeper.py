#!/usr/bin/env python3

import os
import argparse
import logging
import re
import shutil
from datetime import datetime

def setup_logging(log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Check if the logger already has handlers
    if not logger.handlers:
        handler = logging.FileHandler('beekeeper.log')
        handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Update the log level of existing handlers
        for handler in logger.handlers:
            handler.setLevel(log_level)

def extract_date_from_filename(filename):
    # Define patterns for the dates
    patterns = [
        r'\d{4}-\d{2}-\d{2}',             # 2023-04-12
        r'\d{4}_\d{2}_\d{2}',             # 2023_04_12
        r'\d{8}',                         # 20231224
        r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', # 2023-04-12_15-30
        r'\d{4}_\d{2}_\d{2}_\d{2}_\d{2}', # 2023_04_12_15_30
        r'\d{8}_\d{4}',                   # 20231224_1530
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                # Parse the matched date string using datetime.strptime
                if len(match.group()) == 8:
                    return datetime.strptime(match.group(), '%Y%m%d').date()
                else:
                    return datetime.strptime(match.group(), '%Y-%m-%d_%H-%M').date()
            except ValueError:
                continue  # If parsing fails, try the next pattern

    return None  # Return None if no valid date is found

def should_preserve(file_date, args, all_file_dates):
    current_date = datetime.now().date()
    file_age = (current_date - file_date).days

    # Daily preservation
    if file_age <= args.max_age_daily:
        return True

    # Weekly preservation
    if file_age <= args.max_age_weekly:
        file_iso_week = file_date.isocalendar()[:2]  # (year, week)
        # Preserve if it's the latest file in its ISO week
        if not any(
            other_file_date.isocalendar()[:2] == file_iso_week and other_file_date > file_date
            for other_file_date in all_file_dates
        ):
            return True

    # Monthly preservation
    if file_age <= args.max_age_monthly:
        if file_date.month == current_date.month and file_date.year == current_date.year:
            return True

    # Yearly preservation
    if file_age <= args.max_age_yearly:
        if file_date.year == current_date.year:
            return True

    return False

def delete_old_backups(args):
    setup_logging(getattr(logging, args.log_level))

    files_deleted = 0
    directories_deleted = 0
    potential_deletes = 0
    errors = 0
    total_files = 0
    preserved_files = set()
    all_file_dates = []

    filepath = args.filepath
    dry_run = args.dry_run

    all_files_and_dirs = [os.path.join(filepath, f) for f in os.listdir(filepath)]

    # Collect all file and directory dates
    for file_path in all_files_and_dirs:
        if args.use_filename:
            extracted_date = extract_date_from_filename(os.path.basename(file_path))
            if extracted_date:
                all_file_dates.append(extracted_date)
                continue  # Skip to the next file or directory if the date is extracted

        file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()
        all_file_dates.append(file_date)

    for file_path in all_files_and_dirs:
        total_files += 1
        file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()

        if should_preserve(file_date, args, all_file_dates):
            preserved_files.add(file_path)
        else:
            if dry_run:
                potential_deletes += 1
                logging.info(f"Dry run - {'Directory' if os.path.isdir(file_path) else 'File'} would be deleted: {file_path}")
            else:
                try:
                    if os.path.isdir(file_path) and not os.path.islink(file_path):
                        shutil.rmtree(file_path)  # Recursively delete directory
                        directories_deleted += 1
                        logging.info(f"Directory deleted: {file_path}")
                    else:
                        os.remove(file_path)  # Delete file
                        files_deleted += 1
                        logging.info(f"File deleted: {file_path}")
                except OSError as e:
                    errors += 1
                    logging.error(f"Error deleting {'directory' if os.path.isdir(file_path) else 'file'}: {file_path} - {str(e)}")

    return total_files, files_deleted, directories_deleted, potential_deletes, errors, preserved_files

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='''BeeKeeper efficiently manages and deletes backups, adhering to a configurable Grandfather-Father-Son (GFS) retention policy.
It offers precise control over backup retention periods across different levels (daily, weekly, monthly, yearly) and
providing a robust solution for optimizing disk space and maintaining essential backups.''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('filepath', help='Path to the files', nargs='?')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (does not delete files)')
    parser.add_argument('--use-filename', action='store_true', help='Use date from filename to determine age (default: disabled)')
    parser.add_argument('--max-age-daily', type=int, default=30, metavar='DAYS', help='Maximum age for daily backups (default: 30)')
    parser.add_argument('--max-age-weekly', type=int, default=365, metavar='DAYS', help='Maximum age for weekly backups (default: 365)')
    parser.add_argument('--max-age-monthly', type=int, default=1095, metavar='DAYS', help='Maximum age for monthly backups (default: 1095)')
    parser.add_argument('--max-age-yearly', type=int, default=3*365, metavar='DAYS', help='Maximum age for yearly backups (default: 3*365)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set the logging level (default: INFO)')
    args = parser.parse_args()

    if args.max_age_daily > args.max_age_weekly or args.max_age_weekly > args.max_age_monthly or args.max_age_monthly > args.max_age_yearly:
        parser.error("Age thresholds must be increasing (daily < weekly < monthly < yearly)")

    return args, parser

def print_summary(total_files, files_deleted, directories_deleted, potential_deletes, errors, preserved_files, args):
    if args.dry_run:
        print(f"Total files scanned: {total_files}")
        print(f"Matched items: {len(preserved_files)}")
        print(f"Potential deletions: {potential_deletes} (Dry run - no files or directories were actually deleted)")
    else:
        print(f"Total files scanned: {total_files}")
        print(f"Matched items: {len(preserved_files)}")
        print(f"Deleted files: {files_deleted}")
        print(f"Deleted directories: {directories_deleted}")
        if errors:
            print(f"Errors encountered: {errors}")

    print("\nOptions used:\n─────────────")
    print(f"- Dry run: {'Yes' if args.dry_run else 'No'}")
    print(f"- Use filename for date: {'Yes' if args.use_filename else 'No'}")

def main():
    args, parser = parse_arguments()
    setup_logging(getattr(logging, args.log_level))

    if not args.filepath:
        parser.print_help()
        parser.exit()

    total_files, files_deleted, directories_deleted, potential_deletes, errors, preserved_files = delete_old_backups(args)
    print_summary(total_files, files_deleted, directories_deleted, potential_deletes, errors, preserved_files, args)

if __name__ == '__main__':
    main()
