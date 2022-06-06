import sys
from PyQt5 import QtWidgets
from PyQt5 import uic
from model_sql_ui import conn, loginInfo


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super(LoginWindow, self).__init__()
        uic.loadUi("./model_login.ui", self)  # ui파알을 위젯에 할당할 때 loadUi

        self.user_list = loginInfo()
        self.comboBox_name.addItems(self.user_list)

        self.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    app.exec_()