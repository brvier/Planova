from kivy.utils import platform
from libs.applibs.models import DailiesData


ORG_PATH = os.path.expanduser("~/Org")
if platform == "android":
    from android import mActivity
    context = mActivity.getApplicationContext()
    ORG_PATH = context.getExternalMediaDirs()[0].getPath()

class ReviewGenerator:
    def generateReview(self):

        model = DailiesData()
        dt = datetime.datetime.now()

        """
            # Event 

            # Undone todo

            # 13/12/2025

            # 14/12/2025
        """

        events = model.get_future_events()

if __name__ == "__main__":
    ReviewGenerator()

