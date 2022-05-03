import sys
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

# from model_sql_ui import *

form_class = uic.loadUiType("./model_manage_main.ui")[0]


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        # tableWidget
        self.tableWidget.setSpan(0,0,1,6)
        self.tableWidget.setItem(0,0, QTableWidgetItem("조회된 데이터가 없습니다."))
        self.btn_search.clicked.connect(self.getDefaultTableData)
        self.btn_next.clicked.connect(lambda: self.tablePaging("next"))
        self.btn_prev.clicked.connect(lambda: self.tablePaging("prev"))

        # modelData
        self.tablePageNo = 1
        self.modelDataLen = 0

        self.show()
        print(dir(self))

    def getDefaultTableData(self):
        self.tableWidget.removeRow(0)
        model_data = [[1,2,3,4,5,6], [1,2,3,4,5,6], [1,2,3,4,5,6]]
        # model_data = get_model_list(self.tablePageNo)
        self.modelDataLen = len(model_data)
        self.modelDataUpdate(model_data)

    def tablePaging(self, v_btn_type):
        if v_btn_type == "next":
            if self.tablePageNo == self.modelDataLen:
                QMessageBox.about(self, "알림", "현재 페이지가 마지막 페이지입니다.")
                return
            else:
                self.tablePageNo += 1
        else:
            if self.tablePageNo == 1:
                QMessageBox.about(self, "알림", "현재 페이지가 처음 페이지입니다.")
                return
            else:
                self.tablePageNo -= 1

        self.tableWidget.setRowCount(0)
        model_data = [[10,20,30,40,50,60], [99,88,77,66,55,44], [7,6,5,4,3,2]]
        # model_data = get_model_list(self.tablePageNo)
        self.modelDataUpdate(model_data)

    def modelDataUpdate(self, v_model_data):
        for m_idx, m_row in enumerate(v_model_data):
            self.tableWidget.insertRow(m_idx)
            for r_idx, r_data in enumerate(m_row):
                self.tableWidget.setItem(m_idx, r_idx, QTableWidgetItem(str(r_data)))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
