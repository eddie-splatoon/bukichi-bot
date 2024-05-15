import sqlite3
import time

from datetime import datetime as dt, timezone as tz
from zoneinfo import ZoneInfo


class LogRepository:
    def __init__(self):
        def adapt_datetime(ts):
            return time.mktime(ts.timetuple())

        now = self.get_current_timestamp().strftime('%Y%m%d_%H%M%S')
        sqlite3.register_adapter(dt, adapt_datetime)
        self.conn = sqlite3.connect(f'database/bukichi_bot.{now}.db',
                                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']

        self.cursor = self.conn.cursor()
        sql = f"""
        CREATE TABLE vc(
            id integer primary key autoincrement,
            user text,
            channel text,
            event text,
            message text,
            timestamp datetime
        )
        """
        self.cursor.execute(sql)

    def on_join(self, user, channel):
        self.save(user, channel, 'joined', '')

    def on_leave(self, user, channel):
        self.save(user, channel, 'left', '')

    def on_message_sent(self, user, channel, message):
        self.save(user, channel, 'message-sent', message)

    def on_message_edited(self, user, channel, message):
        self.save(user, channel, 'message-edited', message)

    def on_message_deleted(self, user, channel, message):
        self.save(user, channel, 'message-deleted', message)

    def on_message_bulk_deleted(self, user, channel, message):
        self.save(user, channel, 'message-bulk-deleted', message)

    def save(self, user, channel, event, message):
        timestamp = self.get_current_timestamp()
        self.cursor.execute(f'INSERT INTO vc(user, channel, event, message, timestamp) VALUES(?, ?, ?, ?, ?)',
                            (user, channel, event, message, timestamp))
        self.conn.commit()

    @staticmethod
    def get_current_timestamp():
        return dt.now(ZoneInfo("Asia/Tokyo"))
