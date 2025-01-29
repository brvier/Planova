from time import time
from jnius import cast, autoclass


Intent = autoclass('android.content.Intent')
AlarmReceiver = autoclass('fr.rvier.planova.AlarmReceiver')
mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
Intent = autoclass('android.content.Intent')
AlarmManager = autoclass('android.app.AlarmManager')
PendingIntent = autoclass('android.app.PendingIntent')
Context = autoclass('android.content.Context')


class MAlarmManager:
    def __init__(self):
        pass

    def start(self, time):
        self.create_alarm(time)

    def create_alarm(self, seconds):

        context = mActivity.getApplicationContext()

        alarmSetTime = int(round(time() * 1000)) + 1000 * seconds
        alarmIntent = Intent()
        alarmIntent.setClass(context, AlarmReceiver)
        alarmIntent.setAction("fr.rvier.planova.ACTION_START_EVENT_ALARM")

        pendingIntent = PendingIntent.getBroadcast(
            context, 181864, alarmIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_ONE_SHOT
        )

        alarm = cast(
            AlarmManager, context.getSystemService(Context.ALARM_SERVICE))

        alarm.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP, alarmSetTime, pendingIntent)
