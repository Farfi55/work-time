#!/usr/bin/env python3
import datetime
import sys

date_format = "%d %b %y"

from typing import List

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



def show_week():
    # show a recap of every day of the week, even if there is no data
    today = datetime.datetime.now()
    week = today.isocalendar()[1]
    year = today.year

    total_time = 0

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

def show_month():
    # show a recap of every day of the month, even if there is no data
    today = datetime.datetime.now()
    month = today.month
    year = today.year

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



def usage():
    print("Usage: time-tracker.py <command>")
    print("Commands:")

    print("  clock in [HH:MM]\t Clock in at the current time or at the specified time")
    
    print("  clock out [HH:MM]\t Clock out at the current time or at the specified time")
    
    print("  help\t\t\t Show this help message")
    
    print("  today\t\t\t Show the time worked today")
    print("  week [week]\t\t Show the time worked this week or the specified one")
    print("  month [month]\t\t Show the time worked this month or the specified one")
    print("  all\t\t\t Show the total time worked")

    print("  edit\t\t\t Open the data file in the default editor")

    print("  update\t\t Update the time data")



# decide what to do based on the arguments
time_data: List['TimeRow'] = []

def main():
        read_data()

        if len(sys.argv) == 1:
            show_today()
            return

        command = sys.argv[1]

        if command == "clock":
            if len(sys.argv) == 2:
                print("Missing argument")
                return

            if len(sys.argv) == 4:
                time = datetime.datetime.strptime(sys.argv[3], "%H:%M")
                time = datetime.datetime.combine(datetime.datetime.now().date(), time.time())
            else:
                time = None

            if sys.argv[2] == "in":
                clock_in(time)
            elif sys.argv[2] == "out":
                clock_out(time)
            else:
                print("Invalid command")
                usage()
            return
        elif command == "today":
            show_today()
        elif command == "week":
            show_week()
        elif command == "month":
            show_month()
        elif command == "all":
            show_all()
        elif command == "update":
            update(skip_whem_no_intervals=True, interactive=True)
        elif command == "help":
            usage()
        else:
            print("Invalid command")
            usage()
            return

FILE_PATH = "/home/farfi/Dev/sebyone/time-tracker.csv"

with open(FILE_PATH, "r+") as file:
    main()
