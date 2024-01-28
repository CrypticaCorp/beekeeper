#!/usr/bin/env python3

import os
import argparse
import logging
from datetime import datetime
from collections import defaultdict

def setup_logging(log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)  # Set log level based on user input
    
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

def get_week_num(file_date):
    return file_date.isocalendar()[1]

def get_month_num(file_date):
    return file_date.month

def get_year_num(file_date):
    return file_date.year

def get_most_recent_in_periods(period_files):
    most_recent_files = []
    for period in period_files:
        files = period_files[period]
        files.sort(key=os.path.getmtime)
        if files:
            most_recent_files.append(files[-1])
    return most_recent_files

def delete_old_backups(args):
    setup_logging(getattr(logging, args.log_level))

    files_deleted = 0
    potential_deletes = 0
    errors = 0
    total_files = 0
    deleted_files = []

    filepath = args.filepath
    dry_run = args.dry_run
    use_filename = args.use_filename
    recursive = args.recursive
    clean_folders = args.clean_folders
    follow_symlinks = args.follow_symlinks
    max_age_daily = args.max_age_daily
    max_age_weekly = args.max_age_weekly
    max_age_monthly = args.max_age_monthly
    max_age_yearly = args.max_age_yearly

    if recursive:
        all_files = []
        for dirpath, _, filenames in os.walk(filepath, followlinks=follow_symlinks):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                all_files.append((file_path, os.path.getmtime(file_path)))
    else:
        all_files = [(os.path.join(filepath, f), os.path.getmtime(os.path.join(filepath, f))) 
                    for f in os.listdir(filepath) 
                    if os.path.isfile(os.path.join(filepath, f))]

    # Sort the files by modification time, newest first
    all_files.sort(key=lambda x: x[1], reverse=True)

    # Extract file paths, discard modification times
    all_files = [file[0] for file in all_files]

    week_files = defaultdict(list)
    month_files = defaultdict(list)
    year_files = defaultdict(list)
    last_days_files = []

    current_date = datetime.now().date()

    for file in all_files:
        total_files += 1

        if use_filename:
            date_part = [part for part in os.path.basename(file).split('_') if '-' in part or part.isdigit()]
            if not date_part:
                continue
            date_part = date_part[0]
            try:
                file_date = datetime.strptime(date_part, '%Y%m%d').date()
            except ValueError:
                try:
                    file_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                except ValueError:
                    continue
        else:
            file_date = datetime.fromtimestamp(os.path.getmtime(file)).date()

        file_age = (current_date - file_date).days

        if file_age <= max_age_daily:
            last_days_files.append(file)
        elif file_age <= max_age_weekly:
            week_files[get_week_num(file_date)].append(file)
        elif file_age <= max_age_monthly:
            month_files[get_month_num(file_date)].append(file)
        elif file_age <= max_age_yearly:
            year_files[get_year_num(file_date)].append(file)

    preserved_files = set(get_most_recent_in_periods(week_files) +
                          get_most_recent_in_periods(month_files) +
                          get_most_recent_in_periods(year_files) +
                          last_days_files)

    # Delete files
    for file in all_files:
        if file not in preserved_files:
            if dry_run:
                potential_deletes += 1
                deleted_files.append(file)
                logging.info(f"Dry run - File would be deleted: {file}")
            else:
                try:
                    os.remove(file)
                    files_deleted += 1
                    deleted_files.append(file)
                    logging.info(f"File deleted: {file}")
                except OSError as e:
                    errors += 1
                    logging.error(f"Error deleting file: {file} - {str(e)}")

    if clean_folders and recursive:
        for root, dirs, files in os.walk(filepath, topdown=False, followlinks=follow_symlinks):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if not os.listdir(dir_path):
                    if dry_run:
                        print(f"Would remove empty directory: {dir_path}")
                    else:
                        try:
                            os.rmdir(dir_path)
                            logging.info(f"Removed empty directory: {dir_path}")
                        except Exception as e:
                            errors += 1
                            logging.error(f"Error removing directory: {dir_path} - {str(e)}")

    return total_files, files_deleted, potential_deletes, errors, preserved_files

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='''BeeKeeper efficiently manages and deletes backups, adhering to a configurable Grandfather-Father-Son (GFS) retention policy.
It offers precise control over backup retention periods across different levels (daily, weekly, monthly, yearly) and
providing a robust solution for optimizing disk space and maintaining essential backups.''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('filepath', help='Path to the files', nargs='?')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (does not delete files)')
    parser.add_argument('--use-filename', action='store_true', help='Use filename to determine file age')
    parser.add_argument('--recursive', action='store_true', help='Recursively search directories for files to delete')
    parser.add_argument('--clean-folders', action='store_true', help='Remove empty folders after file deletion (requires --recursive)')
    parser.add_argument('--follow-symlinks', action='store_true', help='Follow symbolic links (default is not to follow)')
    parser.add_argument('--max-age-daily', type=int, default=30, metavar='DAYS', help='Maximum age for daily backups (default: 30)')
    parser.add_argument('--max-age-weekly', type=int, default=365, metavar='DAYS', help='Maximum age for weekly backups (default: 365)')
    parser.add_argument('--max-age-monthly', type=int, default=1095, metavar='DAYS', help='Maximum age for monthly backups (default: 1095)')
    parser.add_argument('--max-age-yearly', type=int, default=3*365, metavar='DAYS', help='Maximum age for yearly backups (default: 3*365)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set the logging level (default: INFO)')
    args = parser.parse_args()

    if args.max_age_daily > args.max_age_weekly or args.max_age_weekly > args.max_age_monthly or args.max_age_monthly > args.max_age_yearly:
        parser.error("Age thresholds must be increasing (daily < weekly < monthly < yearly)")
    
    return args, parser

def print_summary(total_files, deleted_count, potential_deletes, errors, preserved_files, args):
    if args.dry_run:
        print(f"Total files scanned: {total_files}")
        print(f"Matched files: {len(preserved_files)}")
        print(f"Potential files to delete: {potential_deletes} (Dry run - no files were actually deleted)")
    else:
        print(f"Total files scanned: {total_files}")
        print(f"Matched files: {len(preserved_files) + deleted_count}")
        print(f"Deleted files: {deleted_count}")
        if errors:
            print(f"Errors encountered: {errors}")

    print("\nOptions used:\n─────────────")
    print(f"- Dry run: {'Yes' if args.dry_run else 'No'}")
    print(f"- Use filename for date: {'Yes' if args.use_filename else 'No'}")
    print(f"- Recursive: {'Yes' if args.recursive else 'No'}")
    print(f"- Clean empty folders: {'Yes' if args.clean_folders else 'No'}")
    print(f"- Follow symbolic links: {'Yes' if args.follow_symlinks else 'No'}")

def main():
    args, parser = parse_arguments()
    setup_logging(getattr(logging, args.log_level))  # Use the log level from args
    
    if not args.filepath:
        parser.print_help()
        parser.exit()
        
    total_files, deleted_count, potential_deletes, errors, preserved_files = delete_old_backups(args)
    print_summary(total_files, deleted_count, potential_deletes, errors, preserved_files, args)

if __name__ == '__main__':
    main()
