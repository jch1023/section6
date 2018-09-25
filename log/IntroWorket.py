from pyQt5.QtCore import Qobject, pyqtSignal, pyqtSlot
from PyQt5.QtMultimedia import QSound

class IntroWorker(Qobject):
    startMsg = pyqtSignal(str, str)
    @pyqtSlot
    def playBgm(self):
        self.intro = 
