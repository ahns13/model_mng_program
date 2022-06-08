import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5 import uic
from model_sql_ui import conn, loginInfo, updatePassword, loginExec
from PyQt5.QtWidgets import QMessageBox, QApplication


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super(LoginWindow, self).__init__()
        uic.loadUi("./model_login.ui", self)  # ui파알을 위젯에 할당할 때 loadUi

        # self.main_window = v_main_window
        self.user_list = loginInfo()
        self.comboBox_name.addItems(self.user_list)

        self.btn_pw_update.clicked.connect(self.openPasswordUpdater)
        self.lineEdit_pw.returnPressed.connect(self.loginExec)
        self.btn_login.clicked.connect(self.loginExec)

        # block - window close/minimize/maximize button
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint)

        self.show()

    def openPasswordUpdater(self):
        try:
            if loginExec(self.comboBox_name.currentText(), self.lineEdit_pw.text()):
                # self.hide()
                password_window = PasswordWindow(self, self.comboBox_name.currentText())
                password_window.exec_()
            elif not self.lineEdit_pw.text():
                QMessageBox.about(self, "알림", "기 등록된 비밀번호를 입력한 후에 수정할 수 있습니다.")
            else:
                QMessageBox.about(self, "알림", "비밀번호가 맞지 않습니다.")
        except Exception as e:
            QMessageBox.critical(self, "Error", e.args[0])

    def loginExec(self):
        user_name = self.comboBox_name.currentText()
        if loginExec(user_name, self.lineEdit_pw.text()):
            main_window = next((win for win in QApplication.topLevelWidgets() if win.objectName() == "MainWindow"))
            main_window.login_user_name = user_name
            self.close()
        else:
            QMessageBox.about(self, "알림", "비밀번호가 맞지 않습니다.")

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            conn.close()
            sys.exit()


class PasswordWindow(QtWidgets.QDialog):
    def __init__(self, v_login_window, v_user_name):
        super(PasswordWindow, self).__init__()
        uic.loadUi("./model_login_pw.ui", self)

        self.user_name = v_user_name
        self.login_window = v_login_window

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.btn_pw_save.clicked.connect(self.updatePassword)

        # block - window close/minimize/maximize button
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.show()

    def updatePassword(self):
        try:
            input_pw = self.lineEdit_pw_input.text()
            check_pw = self.lineEdit_pw_check.text()
            if input_pw and input_pw == check_pw:
                if updatePassword(self.user_name, input_pw):
                    QMessageBox.about(self, "알림", "비밀번호 수정 완료.")
                    conn.commit()
                    self.login_window.lineEdit_pw.setText("")
                    self.close()
                else:
                    QMessageBox.about(self, "알림", "비밀번호 저장에 오류가 있습니다. 관리자에게 문의해 주세요.")
            else:
                QMessageBox.about(self, "알림", "입력한 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
        except Exception as e:
            QMessageBox.critical(self, "Error", e.args[0])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    app.exec_()