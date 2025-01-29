import sqlite3
import re
import datetime
import os
import logging
from dateutil.relativedelta import relativedelta

from kivy.utils import platform
logger = logging.getLogger("Planova.model")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


cache_path = os.path.expanduser('~/.config/planova/cache.db')
if platform == "android":
    from android import mActivity
    context = mActivity.getApplicationContext()
    cache_path = os.path.join(
        context.getExternalFilesDir(None).getPath(), 'cache.db')


class DailiesData:
    def __init__(self):
        if not os.path.exists(os.path.dirname(cache_path)):
            os.makedirs(os.path.dirname(cache_path))

        self.conn = sqlite3.connect(cache_path)
        cursor = self.conn.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS files (filepath TEXT PRIMARY KEY, mtime INTEGER, datetime INTEGER)')

        cursor.execute('''CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY,
                    status TEXT,
                    content TEXT,
                    filepath TEXT,
                    line_idx INTEGER,
                    todo_datetime INTEGER,
                    FOREIGN KEY (filepath) REFERENCES files(filepath) ON DELETE CASCADE
                  )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    event_datetime INTEGER,
                    filepath TEXT,
                    line_idx INTEGER,
                    content TEXT,
                    FOREIGN KEY (filepath) REFERENCES files(filepath) ON DELETE CASCADE
                  )''')
        self.conn.commit()

    def get_dailies_idx_for_month(self, year, month):
        cursor = self.conn.cursor()
        d = datetime.datetime(year=year, month=month,
                              day=1, hour=0, minute=0, second=0)
        print(d, d + relativedelta(months=+1))
        cursor.execute("SELECT datetime FROM files where datetime >= ? and datetime < ?",
                       [d.timestamp(),
                        (d + relativedelta(months=+1)).timestamp()])
        rows = cursor.fetchall()
        return set([str(datetime.datetime.fromtimestamp(d[0]).day) for d in rows])

    def get_events_idx_for_month(self, year, month):
        cursor = self.conn.cursor()
        d = datetime.datetime(year=year, month=month,
                              day=1, hour=0, minute=0, second=0)
        cursor.execute("SELECT event_datetime FROM events where event_datetime >= ? and event_datetime < ?",
                       [d.timestamp(),
                        (d + relativedelta(months=+1)).timestamp()])
        rows = cursor.fetchall()
        return set([str(datetime.datetime.fromtimestamp(d[0]).day) for d in rows])

    def get_todos_idx_for_month(self, year, month):
        cursor = self.conn.cursor()
        d = datetime.datetime(year=year, month=month,
                              day=1, hour=0, minute=0, second=0)
        cursor.execute("SELECT todo_datetime FROM todos where todo_datetime >= ? "
                       "and todo_datetime < ? and status != 'DONE'",
                       [d.timestamp(),
                        (d + relativedelta(months=+1)).timestamp()])
        rows = cursor.fetchall()
        return set([str(datetime.datetime.fromtimestamp(d[0]).day) for d in rows])

    def get_future_events(self, dt):
        cursor = self.conn.cursor()
        cursor.execute("SELECT content, filepath, line_idx, event_datetime FROM events where event_datetime >= ?",
                       [dt.timestamp(),])
        rows = cursor.fetchall()
        return rows


    def get_todos(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT status , content , filepath , line_idx, todo_datetime FROM todos"
                       " WHERE status != 'DONE'",
                       [])
        rows = cursor.fetchall()
        return rows

    def clean(self, filepath):
        cursor = self.conn.cursor()
        cursor.execute('delete from files where filepath = ?', (filepath,))
        cursor.execute('delete from events where filepath = ?', (filepath,))
        cursor.execute('delete from todos where filepath = ?', (filepath,))
        self.conn.commit()

    def is_newer(self, filepath, mtime):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT mtime FROM files where filepath = ? LIMIT 1", [filepath,])
        first_row = cursor.fetchone()
        if first_row is None:
            return True
        print('first_row:', first_row)
        return mtime > first_row[0]

    def db_insert_event(self, filepath, line_idx, dt, content):
        cursor = self.conn.cursor()
        if content.startswith("- "):
            content=content[2:]
        cursor.execute('INSERT INTO events (filepath, line_idx, event_datetime, content) VALUES (?,?,?,?)',
                       (filepath, line_idx, dt.timestamp(), content))
        self.conn.commit()

    def db_insert_files(self, filepath, dt):
        cursor = self.conn.cursor()
        mtime = int(os.stat(filepath).st_mtime)
        if dt is None:
            dt = 0
        else:
            dt = dt.timestamp()
        cursor.execute(
            'INSERT INTO files (filepath,mtime, datetime) VALUES (?,?,?)', (filepath, mtime, dt))
        self.conn.commit()

    def db_insert_todo(self, filepath, line_idx, dt, t, content):
        if not content:
            return

        if t == ' ':
            ty = 'TODO'
        elif t == '-':
            ty = 'WAIT'
        else:
            ty = 'DONE'

        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO todos (filepath, line_idx, todo_datetime, status, content) VALUES (?,?,?,?,?)',
                       (filepath, line_idx, dt.timestamp(), ty, content))
        self.conn.commit()

    def parse_folder(self, folderpath):
        try:
            for f in os.listdir(folderpath):
                if f.endswith('.md'):
                    print(f"Parsing {f}")
                    fpth = os.path.join(folderpath, f)
                    if self.is_newer(fpth, int(os.stat(fpth).st_mtime)):
                        self.parse_file(fpth)
        except FileNotFoundError:
            os.makedirs(folderpath)

    def parse_file(self, filepath):
        print(f'parsing {filepath}')
        self.clean(filepath)

        daily_pattern = r'(\d{4}\d{2}\d{2}).md'
        filename = os.path.basename(filepath)

        daily_match = re.match(daily_pattern, filename)
        if daily_match:
            daily_date = datetime.datetime.strptime(
                daily_match.group(1), '%Y%m%d')
            daily_datestr = daily_date.strftime("%Y-%m-%d")
        else:
            daily_date = None
            daily_datestr = None

        fullevent_pattern = r'(.*)@(\d{4}-\d{2}-\d{2} \d{2}:\d{2})(.*)'
        event_pattern = r'(.*)@(\d{2}:\d{2})\s(.*)'
        todo_pattern = r'.*- \[( |x|-)\](.*)'

        with open(filepath, 'r') as fh:
            for line_idx, line in enumerate(fh.readlines()):
                if (daily_date is not None) and (daily_datestr is not None):
                    event_matches = re.match(event_pattern, line)
                    # Match daily events
                    if event_matches:
                        self.db_insert_event(filepath, line_idx, datetime.datetime.strptime(
                            daily_datestr + " " + event_matches.group(2), "%Y-%m-%d %H:%M"),
                            event_matches.group(1) + event_matches.group(3))
                
                    # Match todo
                    todo_matches = re.match(todo_pattern, line)
                    if todo_matches:
                        if todo_matches.group(2):
                            self.db_insert_todo(filepath, line_idx, datetime.datetime.strptime(
                                daily_datestr, "%Y-%m-%d"), todo_matches.group(1), todo_matches.group(2))

                else:
                    # Match events
                    fullevent_matches = re.match(fullevent_pattern, line)
                    if fullevent_matches:
                        self.db_insert_event(filepath, line_idx, datetime.datetime.strptime(
                            fullevent_matches.group(2), "%Y-%m-%d %H:%M"),
                            fullevent_matches.group(1) + fullevent_matches.group(3))

        self.db_insert_files(filepath, daily_date)
