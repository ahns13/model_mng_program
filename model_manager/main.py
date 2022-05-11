import sys, math
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import *

from model_sql_ui import *

form_class = uic.loadUiType("./model_manage_main.ui")[0]


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # tableWidget
        self.tableColCount = self.tableWidget.columnCount()
        self.tableWidget.setColumnWidth(0, 80)
        self.tableWidget.setColumnWidth(1, 60)
        self.tableWidget.setColumnWidth(2, 120)
        self.tableWidget.setColumnWidth(3, 120)
        self.tableWidget.setColumnWidth(4, 80)
        self.tableWidget.setColumnWidth(5, 130)
        self.tableWidget.setColumnWidth(6, 180)

        self.noSearchMsg()
        self.btn_search.clicked.connect(self.getDefaultTableData)
        self.btn_next.clicked.connect(lambda: self.tablePaging("next"))
        self.btn_prev.clicked.connect(lambda: self.tablePaging("prev"))

        # lineEdit
        # self.lineEdit.returnPressed.connect(self.getDefaultTableData)

        # modelData
        self.tablePageNo = 0
        self.modelDataLen = 0
        self.maxPageSize = None
        self.pageSize = 20

        # comboBox
        self.combo_data_profile = get_comboBox_list_a("PROFILE")
        self.combo_data_career = get_comboBox_list_career()
        self.combo_data_contact = get_comboBox_list_a("CONTACT")
        self.combo_data_contract = get_comboBox_list_a("CONTRACT")
        # self.combo_other = get_comboBox_list_a("OTHER")

        list_view = QListView()
        self.combo_career.setView(list_view)

        self.combo_profile.addItems(self.combo_data_profile[0])
        self.combo_career.addItems(self.combo_data_career[0])
        self.combo_contact.addItems(self.combo_data_contact[0])
        self.combo_contract.addItems(self.combo_data_contract[0])

        self.combo_career.setStyleSheet('''
            QComboBox QAbstractItemView::item { min-width: 100px; min-height: 30px;}
            QListView::item:selected { color: red; background-color: lightgray; min-width: 1000px;}"
            ''')
        # QComboBox { max-width: 120px; min-height: 30px;}

        cursor.close()

        self.show()
        print(dir(self))

    def tableDataInit(self):
        self.tablePageNo = 0
        self.modelDataLen = 0
        self.maxPageSize = None
        self.combo_page.clear()

    def getDefaultTableData(self):
        self.tableWidget.removeRow(0)
        self.tablePageNo = 1
        # model_data = [[1,2,3,4,5,6], [1,2,3,4,5,6], [1,2,3,4,5,6]]
        model_data = get_model_list(self.tablePageNo, self.pageSize, {})
        self.modelDataLen = model_data[0][self.tableColCount]
        self.maxPageSize = math.ceil(self.modelDataLen/self.pageSize)
        self.combo_page.clear()
        self.combo_page.addItems([str(x) for x in range(1, self.maxPageSize+1)])
        self.combo_page.activated.connect(lambda: self.tablePaging(None, self.comboBox.currentText()))

        if self.modelDataLen:
            self.modelDataUpdate(model_data)
        else:
            self.noSearchMsg()

    def tablePaging(self, v_btn_type, v_page_no=0):
        if v_btn_type == "next":
            if self.tablePageNo == 0:
                return
            elif self.tablePageNo == self.maxPageSize:
                QMessageBox.about(self, "알림", "현재 페이지가 마지막 페이지입니다.")
                return
            else:
                self.tablePageNo += 1
                self.combo_page.setCurrentIndex(self.tablePageNo-1)
        elif v_btn_type == "prev":
            if self.tablePageNo == 0:
                return
            elif self.tablePageNo == 1:
                QMessageBox.about(self, "알림", "현재 페이지가 처음 페이지입니다.")
                return
            else:
                self.tablePageNo -= 1
                self.combo_page.setCurrentIndex(self.tablePageNo-1)
        elif v_page_no and v_page_no != self.tablePageNo:
            self.tablePageNo = int(v_page_no)

        # model_data = [[10,20,30,40,50,60], [99,88,77,66,55,44], [7,6,5,4,3,2]]
        model_data = get_model_list(self.tablePageNo, self.pageSize, {})
        self.modelDataUpdate(model_data)

    def modelDataUpdate(self, v_model_data):
        self.tableWidget.setRowCount(0)
        for m_idx, m_row in enumerate(v_model_data):
            self.tableWidget.insertRow(m_idx)
            self.tableWidget.setRowHeight(m_idx, 20)
            for r_idx, r_data in enumerate(m_row):
                if r_idx <= self.tableColCount-1:  # get_model_list의 result 칼럼 데이터 제한(total_list x)
                    self.tableWidget.setItem(m_idx, r_idx, QTableWidgetItem(str(r_data if r_data else "")))

    def noSearchMsg(self):
        self.tableDataInit()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setSpan(0, 0, 1, self.tableColCount)
        self.tableWidget.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
        self.tableWidget.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
