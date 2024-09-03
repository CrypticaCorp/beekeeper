#!/usr/bin/env python3

import os
import argparse
import shutil
import logging
import re
from datetime import datetime, timedelta
from collections import defaultdict

def setup_logging(log_level, log_file='beekeeper.log'):
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Check if the logger already has handlers
    if not logger.handlers:
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(log_file)

        # Set log level for handlers
        console_handler.setLevel(log_level)
        file_handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Add formatter to handlers
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logging.info(f"Logging initialized.")
    else:
        # If handlers exist, just update their levels
        for handler in logger.handlers:
            handler.setLevel(log_level)
        logging.info(f"Logging level updated to {log_level}")

def parse_date_from_filename(filename):
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
                    return datetime.strptime(match.group(), '%Y-%m-%d').date()
            except ValueError:
                continue  # If parsing fails, try the next pattern

    return None  # Return None if no valid date is found

def should_preserve(file_date, current_date, args):
    age = (current_date - file_date).days
    reasons = []

    # Daily retention
    if age <= args.max_age_daily:
        reasons.append("daily")

    # Weekly retention
    if args.max_age_daily < age <= args.max_age_weekly:
        reasons.append("weekly")

    # Monthly retention
    if age <= args.max_age_monthly and file_date.day == 1:
        reasons.append("monthly")

    # Yearly retention
    if age <= args.max_age_yearly and file_date.month == 1 and file_date.day == 1:
        reasons.append("yearly")

    return len(reasons) > 0, ", ".join(reasons) if reasons else None

def process_backups(args):
    current_date = datetime.now().date()
    backups = []
    weekly_backups = defaultdict(list)

    # Collect and parse backup dates
    for filename in os.listdir(args.filepath):
        file_path = os.path.join(args.filepath, filename)
        if not os.path.isdir(file_path):
            continue

        if args.use_filename:
            backup_date = parse_date_from_filename(filename)
            if backup_date is None:
                backup_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()
        else:
            backup_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()

        backups.append((filename, backup_date))
        week_number = backup_date.isocalendar()[1]
        year = backup_date.isocalendar()[0]
        weekly_backups[(year, week_number)].append((filename, backup_date))

    # Sort backups by date
    backups.sort(key=lambda x: x[1], reverse=True)

    preserved = []
    deleted = []
    weekly_preserved = set()

    for filename, backup_date in backups:
        keep, reason = should_preserve(backup_date, current_date, args)
        if keep:
            if "weekly" in reason:
                week_key = (backup_date.isocalendar()[0], backup_date.isocalendar()[1])
                if week_key not in weekly_preserved and len(weekly_preserved) < 2:
                    weekly_preserved.add(week_key)
                    preserved.append((filename, backup_date, reason))
                else:
                    deleted.append((filename, backup_date))
            else:
                preserved.append((filename, backup_date, reason))
        else:
            deleted.append((filename, backup_date))

    return preserved, deleted

def print_results(preserved, deleted, args):
    total_backups = len(preserved) + len(deleted)

    print("\n" + "=" * 60)
    print("BeeKeeper Backup Analysis".center(60))
    print("=" * 60 + "\n")

    print(f"Total backups scanned: {total_backups}")
    print(f"Backups to preserve:   {len(preserved)}")
    print(f"Backups to delete:     {len(deleted)}\n")

    # Summary of preserved backups
    print("Summary of Preserved Backups:")
    print("-" * 40)
    retention_types = ['daily', 'weekly', 'monthly', 'yearly']
    max_type_length = max(len(t) for t in retention_types)
    for retention_type in retention_types:
        count = sum(1 for _, _, reason in preserved if retention_type in reason)
        print(f"{retention_type.capitalize():<{max_type_length + 2}}: {count}")
    print()

    # Preserved backups
    print("Preserved backups:")
    print("-" * 60)
    print(f"{'Filename':<30} {'Date':<12} {'Reason':<18}")
    print("-" * 60)
    for filename, date, reason in preserved:
        print(f"{filename:<30} {date!s:<12} {reason:<18}")
    print()

    # Deleted backups (show only first 10)
    print("Backups marked for deletion (showing first 10):")
    print("-" * 60)
    print(f"{'Filename':<30} {'Date':<12}")
    print("-" * 60)
    for filename, date in deleted[:10]:
        print(f"{filename:<30} {date!s:<12}")
    if len(deleted) > 10:
        print(f"... and {len(deleted) - 10} more")
    print()

    # Options used
    print("Options used:")
    print("-" * 60)
    options = [
        ("Dry run", "Yes" if args.dry_run else "No"),
        ("Use filename for date", "Yes" if args.use_filename else "No"),
        ("Max age daily", f"{args.max_age_daily} days"),
        ("Max age weekly", f"{args.max_age_weekly} days"),
        ("Max age monthly", f"{args.max_age_monthly} days"),
        ("Max age yearly", f"{args.max_age_yearly} days")
    ]
    max_option_length = max(len(option[0]) for option in options)
    for option, value in options:
        print(f"{option:<{max_option_length + 2}}: {value}")
    print()

def remove_directory(path):
    """
    Recursively remove a directory and its contents.
    """
    try:
        shutil.rmtree(path)
        logging.info(f"Deleted directory and its contents: {path}")
    except Exception as e:
        logging.error(f"Error deleting directory {path}: {e}")

def delete_backups(args, deleted):
    """
    Delete the backups marked for deletion.
    """
    if args.dry_run:
        print("\nDry run completed. No files were deleted.")
        logging.info("Dry run completed. No files were deleted.")
        return

    total = len(deleted)
    print(f"\nPreparing to delete {total} backup(s).")

    if not args.force:
        confirm = input("Are you sure you want to proceed with deletion? (yes/no): ").lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            logging.info("Deletion cancelled by user.")
            return
    else:
        logging.info("Skipping confirmation due to --force option.")

    logging.info(f"Starting deletion of {total} backup(s)")
    for i, (filename, _) in enumerate(deleted, 1):
        file_path = os.path.join(args.filepath, filename)
        print(f"Deleting {i}/{total}: {filename}")
        remove_directory(file_path)

    print(f"\nDeletion complete. {total} backup(s) processed.")
    logging.info(f"Deletion complete. {total} backup(s) processed.")

def main():
    parser = argparse.ArgumentParser(
        description='''BeeKeeper efficiently manages and deletes backups, adhering to a configurable Grandfather-Father-Son (GFS) retention policy.
It offers precise control over backup retention periods across different levels (daily, weekly, monthly, yearly) and
provides a robust solution for optimizing disk space and maintaining essential backups.

Official repository: https://github.com/CrypticaCorp/beekeeper

For the latest version, bug reports, or contributions, please visit the official repository.''',
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
    parser.add_argument('--log-file', default='beekeeper.log', help='Path to the log file (default: beekeeper.log)')
    parser.add_argument('--force', action='store_true', help='Skip confirmation before deleting backups')
    args = parser.parse_args()

    if not args.filepath:
        parser.print_help()
        return

    # Check if the filepath exists and is accessible
    if not os.path.exists(args.filepath):
        print(f"Error: The specified path '{args.filepath}' does not exist.")
        return
    if not os.path.isdir(args.filepath):
        print(f"Error: The specified path '{args.filepath}' is not a directory.")
        return
    if not os.access(args.filepath, os.R_OK):
        print(f"Error: The specified path '{args.filepath}' is not readable.")
        return

    if args.max_age_daily > args.max_age_weekly or args.max_age_weekly > args.max_age_monthly or args.max_age_monthly > args.max_age_yearly:
        parser.error("Age thresholds must be increasing (daily < weekly < monthly < yearly)")

    setup_logging(getattr(logging, args.log_level), args.log_file)

    logging.info(f"Starting backup analysis for path: {args.filepath}")
    preserved, deleted = process_backups(args)
    logging.info(f"Backup analysis completed. Preserved: {len(preserved)}, Deleted: {len(deleted)}")

    print_results(preserved, deleted, args)

    if not args.dry_run:
        delete_backups(args, deleted)
    else:
        logging.info("Dry run completed. No files were deleted.")

    logging.info("BeeKeeper execution completed.")

if __name__ == "__main__":
    main()
