#!/usr/bin/env python3
import datetime
import sys
import os
import argparse
from typing import List

date_format = "%d %b %y"

VERSION = "0.1.0"
AUTHOR = "Alessio Farfaglia"
REPO = "https://github.com/Farfi55/work-time.git"

class TimeRow:
    def __init__(self, date: datetime.date=None, minutes: int=0, intervals: List['TimeInterval']=None):
        # use datetime to parse the date
        if date is None:
            date = datetime.datetime.now()
        self.date = date
        self.duration_minutes = minutes
        if intervals is None:
            intervals = []
        self.intervals = intervals
    
    def __str__(self):
        return f"Date: {self.formatted_date}, Duration: {format_minutes(self.duration_minutes, False)}, Intervals: {self.intervals}"
    
    def __repr__(self):
        return self.__str__()

    def to_csv(self):
        intervals = ""
        for interval in self.intervals:
            intervals += f";\t{str(interval)}"

        return f"{self.formatted_date};\t{self.formatted_duration}{intervals}"
    
    @property
    def day(self):
        return self.date.day
    
    @property
    def month(self):
        return self.date.month
    
    @property
    def formatted_duration(self):
        return format_minutes(self.duration_minutes, False)
    
    @property
    def formatted_date(self):
        return self.date.strftime(date_format)

    def is_today(self):
        today = datetime.datetime.now()
        return self.date.date() == today.date()
    
    def calculate_total_time(self):
        total = 0
        for interval in self.intervals:
            total += interval.delta()
        return total

class TimeInterval:
    def __init__(self, begin:datetime.datetime=None, end:datetime.datetime=None):
        self.begin = begin
        self.end = end

    
    def delta(self) -> int:
        if self.is_complete():
            return int((self.end - self.begin).total_seconds() // 60)
        elif self.begin is not None and self.begin.date() == datetime.datetime.now().date():
            return int((datetime.datetime.now() - self.begin).total_seconds() // 60)
        else:
            return 0

    def is_complete(self):
        return self.begin is not None and self.end is not None
    
    @property
    def formatted_begin(self):
        return format_time(self.begin) if self.begin is not None else "??:??"
    
    @property
    def formatted_end(self):
        return format_time(self.end) if self.end is not None else "??:??"
    
    @property
    def formatted_delta(self):
        return format_minutes(self.delta(), False)

    def __str__(self):
        return f"{self.formatted_begin} - {self.formatted_end}"
    
    def __repr__(self):
        return self.__str__()

def parse_date(date) -> datetime.date:
    return datetime.datetime.strptime(date, date_format)

def parse_line(line):
    parts = line.strip().split(';')
    date = parse_date(parts[0].strip())

    duration_raw = parts[1].strip()
    duration = to_minutes(duration_raw)
    
    # Extracting the time intervals
    intervals = []
    for interval_raw in parts[2:]:
        (interval_parts) = interval_raw.split(' - ')
        if len(interval_parts) == 2:
            (begin, end) = interval_parts
            interval = TimeInterval()
            
            begin = begin.strip()
            end = end.strip()
            if begin != "??:??":
                interval.begin = datetime.datetime.combine(date.date(), datetime.datetime.strptime(begin, "%H:%M").time())
            if end != "??:??":
                interval.end = datetime.datetime.combine(date.date(), datetime.datetime.strptime(end, "%H:%M").time())
            intervals.append(interval)
        else:
            print(f"Invalid interval: {interval_raw}, from line: {line}")
                    
    return TimeRow(date, duration, intervals)


def read_data(skip_first_line=True):
    # Skip the first line
    if skip_first_line:
        file.readline()
    for line in file:
        time_data.append(parse_line(line))

def write_data():
    file.seek(0)
    file.truncate()
    file.write("date;	duration;	begin - end\n")
    for data in time_data:
        file.write(data.to_csv() + "\n")


def to_minutes(time):
    time = time.split(":")
    return int(time[0]) * 60 + int(time[1])

def format_time(datatime):
    return datatime.strftime("%H:%M")

def format_minutes(minutes, leading_zeroes=True):
    hours = minutes // 60
    minutes = int(minutes) % 60
    if leading_zeroes:
        return f"{hours:02d}:{minutes:02d}"
    else:
        return f"{hours}:{minutes:02d}"

def time_now():
    now = datetime.datetime.now()
    return f"{now.hour:02d}:{now.minute:02d}"
    

# clock in
def clock_in(clock_in_time: datetime.datetime = None):
    today_entry = None

    # check if there is a entry for today
    if len(time_data) > 0:
        last_entry = time_data[-1]

        if last_entry.is_today():
            today_entry = last_entry
        else:
            print("First clock in today,", datetime.datetime.now().strftime(date_format))
            
    if today_entry is None:
        today_entry = TimeRow()
        time_data.append(today_entry)

    
    if len(today_entry.intervals) > 0 and not today_entry.intervals[-1].is_complete():
        print("You have already clocked in")
        return

    if clock_in_time is None:
        clock_in_time = datetime.datetime.now()

    interval = TimeInterval(begin=clock_in_time)

    today_entry.intervals.append(interval)
    today_entry.duration_minutes = today_entry.calculate_total_time()

    print("Clocked in at", format_time(clock_in_time))
    print("Total time:", today_entry.formatted_duration)
    
    write_data()

# clock out

def clock_out(clock_out_time: datetime.datetime = None):
    if len(time_data) == 0:
        print("No data")
        return
    
    today_entry = time_data[-1]
    if not today_entry.is_today():
        print("You have not clocked in today")
        return

    if len(today_entry.intervals) == 0:
        print("You have not clocked in yet")
        return
    
    if today_entry.intervals[-1].is_complete():
        print("You have already clocked out")
        return
    
    if clock_out_time is None:
        clock_out_time = datetime.datetime.now()
    
    if clock_out_time < today_entry.intervals[-1].begin:
        print(f"Invalid clock out time, {format_time(clock_out_time)} is before {format_time(today_entry.intervals[-1].begin)}")
        return

    today_entry.intervals[-1].end = clock_out_time
    today_entry.duration_minutes = today_entry.calculate_total_time()
    
    print("Clocked out at", format_time(clock_out_time))
    print("Total time:", today_entry.formatted_duration)
    write_data()



def show_today():
    if len(time_data) == 0:
        print("No data")
        return
    data = time_data[-1]
    if not data.is_today():
        print("No data for today, last entry:", data.date.strftime(date_format))
        return
    
    running_total_time = data.calculate_total_time()

    print(f"Today: {data.formatted_date} ({data.formatted_duration})")
    for interval in data.intervals:
        print(f"  from {interval.formatted_begin} to {interval.formatted_end} ({interval.formatted_delta})")

    daily_goal = 2 * 60
    progress = int(running_total_time / daily_goal * 100)
    print(f"Running total time: {format_minutes(running_total_time, False)} ({progress}% of daily goal)")



def show_week(week_number=None):
    # show a recap of every day of the week, even if there is no data
    today = datetime.datetime.now()
    week = int(today.strftime("%W"))
    year = today.year

    if week_number is not None:
        week_number = int(week_number)
        if week_number < 0:
            week = week + week_number
        else:
            week = week_number
    

    total_time = 0
    print(f"Week {week} ({year})")
    print(f"{'Day':<10} {'Date':<10} {'Time':<10}")

    for i in range(7):
        day = datetime.datetime.strptime(f"{year}-{week}-{(i+1)%7}", "%Y-%W-%w")
        day_data = None
        for data in time_data:
            if data.date.date() == day.date():
                day_data = data
                total_time += data.duration_minutes
                break
        
        if day_data is None:
            day_data = TimeRow(day)
            time_data.append(day_data)
        
        print(f"{day.strftime('%A'):<10} {day_data.formatted_date}", end="")
        if len(day_data.intervals) == 0:
            print("  ------", end="")
        else:
            print(f"  ({day_data.formatted_duration})", end="")
            for interval in day_data.intervals:
                print(f"  {interval}", end="")
        print()

        if day.date() == today.date():
            break

    print(f"\nTotal time: {format_minutes(total_time, False)}")

def show_month(custom_month=None):
    # show a recap of every day of the month, even if there is no data
    today = datetime.datetime.now()
    month = today.month
    year = today.year

    if custom_month is not None:
        # check if custom month is a number
        try: 
            custom_month = int(custom_month)
            if custom_month < 0:
                month = month + custom_month
            else:
                month = custom_month
        except ValueError:
            # try to check if it is a month name
            try:
                month = datetime.datetime.strptime(custom_month, "%B").month
            except ValueError:
                print("Invalid month")
                return

    total_time = 0

    for i in range(31):
        try:
            day = datetime.datetime.strptime(f"{year}-{month}-{i+1}", "%Y-%m-%d")
        except ValueError:
            break
        day_data = None
        for data in time_data:
            if data.date.date() == day.date():
                day_data = data
                total_time += data.duration_minutes
                break
        
        

        if day_data is None:
            day_data = TimeRow(day)
            time_data.append(day_data)
        
        print(f"{day.strftime('%A'):<10} {day_data.formatted_date}", end="")
        if len(day_data.intervals) == 0:
            print("  ------", end="")
        else:
            print(f"  ({day_data.formatted_duration})", end="")
            for interval in day_data.intervals:
                print(f"  {interval}", end="")
        print()
        if day.date() == today.date():
            break
        
        # extra newline after sunday
        if day.weekday() == 6:
            print()

    print(f"\nTotal time: {format_minutes(total_time, False)}")

def show_all():
    last_date = time_data[0].date
    print(f"   {last_date.strftime('%B')}")
    for data in time_data:
        print(f"{data.formatted_date}  ({data.formatted_duration})", end="")
        for interval in data.intervals:
            print(f"\t{interval}", end="")
        print()
        if data.date.month != last_date.month:
            print(f"\n   {data.date.strftime('%B')}")
        last_date = data.date

def update(skip_whem_no_intervals=True, interactive=False):
    for data in time_data:
        if len(data.intervals) == 0 and skip_whem_no_intervals:
            continue

        old = data.duration_minutes
        new = data.calculate_total_time()
        if old != new:
            print(f"Updating {data.formatted_date} from {format_minutes(old, False)} to {format_minutes(new, False)}")
            if interactive:
                answer = input("Update? [y/N]\n")
                if answer.lower() != "y":
                    print("Skipping")
                    continue
                else:
                    print("Updating")

            data.duration_minutes = new
    print("Done")
    write_data()


# decide what to do based on the arguments
time_data: List['TimeRow'] = []

def edit(editor: str):
    if editor == "os":
        if sys.platform == "linux":
            editor = "xdg-open"
        elif sys.platform == "darwin":
            editor = "open"
        elif sys.platform == "win32":
            editor = "start"
    
    os.system(editor + " " + FILE_PATH)



def main():
    read_data()

    parser = argparse.ArgumentParser(
        prog='worktime',
        description='Track the time spent working and generate reports'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subparser for 'clock' command
    clock_parser = subparsers.add_parser('clock', help='Clock in or out')
    clock_parser.add_argument('direction', choices=['in', 'out'], help='Clock in or out')
    clock_parser.add_argument('time', nargs='?', help='Time in HH:MM format (optional)', default=None)

    # Subparser for 'today' command
    subparsers.add_parser('today', help='Show the time worked today')

    # Subparser for 'week' command
    week_parser = subparsers.add_parser('week', help='Show the time worked this week')
    # -1 -> last week, 0 -> this week, 32 -> week 32
    week_parser.add_argument('week', nargs='?', help='Specify a week (optional)', default=None)

    # Subparser for 'month' command
    month_parser = subparsers.add_parser('month', help='Show the time worked this month')
    # -1 -> last month, 0 -> this month, 12 -> December
    # can also specify the month name
    # august, december, ...
    month_parser.add_argument('month', nargs='?', help='Specify a month (optional)', default=None)

    # Subparser for 'all' command
    subparsers.add_parser('all', help='Show the total time worked')

    # Subparser for 'edit' command, can specify ['code', 'nano', 'vim', ...]
    edit_parser = subparsers.add_parser('edit', help='Open the data file in the default editor')
    edit_parser.add_argument('editor', choices=['code', 'nano', 'vim', 'os'], default='m')

    # Subparser for 'update' command
    subparsers.add_parser('update', help='Update the time data')

    # Subparser for 'version' command
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {VERSION} by {AUTHOR} - {REPO}')




    # Parse arguments
    args = parser.parse_args()

    # Handle the 'clock' command
    if args.command == 'clock':
        if args.time:
            try:
                time = datetime.datetime.strptime(args.time, "%H:%M")
                time = datetime.datetime.combine(datetime.datetime.now().date(), time.time())
            except ValueError:
                print("Invalid time format. Use HH:MM.")
                return
        else:
            time = None

        if args.direction == 'in':
            clock_in(time)
        elif args.direction == 'out':
            clock_out(time)

    # Handle other commands
    elif args.command == 'today':
        show_today()
    elif args.command == 'week':
        show_week(args.week)
    elif args.command == 'month':
        show_month(args.month)
    elif args.command == 'all':
        show_all()
    elif args.command == 'edit':
        edit(args.editor)
    elif args.command == 'update':
        update(skip_whem_no_intervals=True, interactive=True)


FILE_PATH = "/home/farfi/Dev/sebyone/time-tracker.csv"

with open(FILE_PATH, "r+") as file:
    main()

