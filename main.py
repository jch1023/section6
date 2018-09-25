import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QUrl, QThread
from PyQt5 import uic
from lib.YouViewerLayout import Ui_MainWindow
from lib.AuthDialog import AuthDialog
from lib.IntroWorker import IntroWorker
import re
import datetime
import pytube
from PyQt5.QtMultimedia import QSound

#https://www.youtube.com/watch?v=tMvXBTsFYoQ&list=PL9mhQYIlKEhf0DKhE-E59fR-iu7Vfpife&index=2


#form_class = uic.loadUiType("c:/workspace/section6/ui/you_viewer_v1.0.ui")[0]
#anaconda cmd : pyuic5 -x you-viewer-layout.ui -o you_viewer_layout.py
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        #초기화
        self.setupUi(self)
        #초기 잠금
        self.initAuthLock() # 초기화 아랫쪽으로 연결
        #시그널 초기화
        self.initSignal()
        #로그인 관련 변수 선언
        self.user_id = None
        self.user_pw = None
        #재생 여부
        self.is_play = False
        #Youtube 관련 작업
        self.youtu = None
        self.youtb_fsize = 0
        #배경음악 Thread 작업 선언
        self.initIntroThread()
        #QThread 사용 안할 경우
        #QSound.play("C:/workspace/section6/resource/intro.wav")


#기본 Ui 비활성화
    def initAuthLock(self):
        self.previewButton.setEnabled(False)
        self.fileNavButton.setEnabled(False)
        self.streamCombobox.setEnabled(False)
        self.startButton.setEnabled(False)
        self.calendarWidget.setEnabled(False)
        self.urlTextEdit.setEnabled(False)
        self.pathTextEdit.setEnabled(False)
        self.showStatusMsg('인증 안됨')


# 기본 ui 활성화
    def initAuthActive(self):
        self.previewButton.setEnabled(True)
        self.fileNavButton.setEnabled(True)
        self.streamCombobox.setEnabled(True)
        self.calendarWidget.setEnabled(True)
        self.urlTextEdit.setEnabled(True)
        self.pathTextEdit.setEnabled(True)
        self.showStatusMsg('인증 완료')

#상태 표시줄에 메세지 표시
    def showStatusMsg(self, msg):
        self.statusbar.showMessage(msg)

# 버튼 클릭시
# 시그널 초기화
    def initSignal(self):
        self.loginButton.clicked.connect(self.authCheck)
        self.previewButton.clicked.connect(self.load_url)
        self.exitButten.clicked.connect(QtCore.QCoreApplication.instance().quit) #버튼 누르면 종료
        self.webView.loadProgress.connect(self.show_ProgressBrowserLoading)
        self.fileNavButton.clicked.connect(self.selectDownPath)
        self.calendarWidget.clicked.connect(self.append_date)
        self.startButton.clicked.connect(self.downloadYoutb)


# 인트로 쓰레드 초기화 및 활성화
    def initIntroThread(self):
        #worker 선언
        self.introObj = IntroWorker()
        #Qtrhread 선언
        self.introThread = QThread()
        #Worker To thread 전환
        self.introObj.moveToThread(self.introThread)
        #시그널 연결
        self.introObj.startMsg.connect(self.showIntroInfo)
        #Thread 시작 메소드 연결
        self.introThread.started.connect(self.introObj.playBgm)
        #Thread 스타트
        self.introThread.start()

#인트로 쓰레드 signal 실행
    def showIntroInfo(self, username, fileName):
        self.plainTextEdit.appendPlainText("Program Statred by : " + username)
        self.plainTextEdit.appendPlainText("Playing intro infomation is : " + username)
        self.plainTextEdit.appendPlainText(fileName)



# 아이디창
    @pyqtSlot()
    def authCheck(self):
        dlg = AuthDialog()
        dlg.exec_()

        self.user_id = dlg.user_id
        self.user_pw = dlg.user_pw

        # 이 부분에서 필요한 경우 실제 로컬 db 또는 서버로 연동 후
        # 유저 정보 및 사용 유효 기간 체크 코드를 넣어 주세요.
        # code
        #print('id: %s Password: %s' %(self.user_id, self.user_pw))

        if True:
            self.initAuthActive()
            self.loginButton.setText('인증완료')
            self.loginButton.setEnabled(False)
            self.urlTextEdit.setFocus(True)
            self.append_log_msg("login Success")

        else:
            QMessageBox.about(self, "인증오류", "아이디 또는 비밀번호 인증 오류")


    def load_url(self):
        url = self.urlTextEdit.text().strip()
        v = re.compile('^https://www.youtube.com/?') #regex
        if self.is_play: # 플레이중에 중단 버튼
            self.append_log_msg('stop Click')
            self.webView.load(QUrl('about:blank'))
            self.previewButton.setText("재생")
            self.is_play = False
            self.urlTextEdit.clear()
            self.urlTextEdit.setFocus(True)
            self.startButton.setEnabled(False)
            self.streamCombobox.clear()
            self.progressBar_2.setValue(0)
            self.showStatusMsg("인증완료")


        else: # 플레이 중이 아닌 경우
            if v.match(url) is not None:
                self.append_log_msg('Play click')
                self.webView.load(QUrl(url))
                self.showStatusMsg(url + "재생 중")
                self.previewButton.setText("중지")
                self.is_play = True
                self.startButton.setEnabled(True)
                self.initialYouWork(url)


            else:
                QMessageBox.about(self,"URL 형식오류", "Youtube 주소 형식이 아닙니다.")
                self.urlTextEdit.clear()
                self.urlTextEdit.setFocus(True)

    #유튜브
    def initialYouWork(self, url):
        video_list = pytube.YouTube(url)
        #로딩바 계산
        video_list.register_on_progress_callback(self.show_ProgressDownLoading)
        self.youtb = video_list.streams.all()
        self.streamCombobox.clear()
        for q in self.youtb:
            #print(q.itag,q.mime_type,q.abr)
            tmp_list, str_list = [], []
            tmp_list.append(str(q.mime_type or '')) #none 말고 공백
            tmp_list.append(str(q.res or '')) #none 말고 공백
            tmp_list.append(str(q.fps or '')) #none 말고 공백
            tmp_list.append(str(q.abr or '')) #none 말고 공백
            #print(tmp_list)
            # tmp_list 순회 중 if 가 null 이 아닌경우만 x 에 집어 넣어라
            str_list = [x for x in tmp_list if x != '']
            #print('step3', str_list)
            print('join :', ','.join(str_list))
            self.streamCombobox.addItem(','.join(str_list)) #join 함수 검색



# 로그 메세지
    def append_log_msg(self, act):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
        app_msg = self.user_id + ' : ' + act + '- (' +nowDatetime + ')'
        self.plainTextEdit.appendPlainText(app_msg) #insertPlainText #로그창에 입력

        # 활동 로그 저장(또는 db를 사용 추천)
        with open('C:/workspace/section6/log/log.txt','a') as f:
            f.write(app_msg+'\n')
# 로딩바
    @pyqtSlot(int)
    def show_ProgressBrowserLoading(self, v):
        self.progressBar.setValue(v)

    #save to 버튼
    @pyqtSlot()
    def selectDownPath(self):
        #파일 선택 - 파일 업로드 할때
        #fname = QFileDialog.getOpenFileName(self)
        #self.pathTextEdit.setText(fname[0])

        #경로 선택 - 파일 저장 폴더 지정
        fpath = QFileDialog.getExistingDirectory(self, 'Select Directory')
        self.pathTextEdit.setText(fpath)

    #달력 클릭시 날짜 입력
    @pyqtSlot()
    def append_date(self):
        cur_date = self.calendarWidget.selectedDate()
        #print(cur_date)
        print(str(cur_date.year())+'-'+str(cur_date.month())+'-'+str(cur_date.day()))
        self.append_log_msg('Calendar Click') # 로그에 입력

    # 유투브 다운로드 버튼 기능
    @pyqtSlot()
    def downloadYoutb(self):
        down_dir = self.pathTextEdit.text().strip()
        if down_dir is None or down_dir == '' or not down_dir:
            QMessageBox.about(self, '경로 선택','다운로드 받을 경로를 선택하세요.')
            self.pathTextEdit.setFocus(True)
            return None

        self.youtb_fsize = self.youtb[self.streamCombobox.currentIndex()].filesize
        print('fsize', self.youtb_fsize)
        self.youtb[self.streamCombobox.currentIndex()].download(down_dir)
        self.append_log_msg('Download Click')

    #유투브 다운로딩 바
    def show_ProgressDownLoading(self, stream, chunk, finle_handle, bytes_remaining):
        print(int(self.youtb_fsize - bytes_remaining))
        print('bytes_remaining', bytes_remaining)
        self.progressBar_2.setValue(int(((self.youtb_fsize - bytes_remaining) / self.youtb_fsize) * 100))
        self.append_log_msg('다운로드 완료')



if __name__ == "__main__":
    app = QApplication(sys.argv)
    you_viewer_main = Main()
    you_viewer_main.show()
    app.exec_()
