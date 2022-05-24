import sys
import copy
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *

from model_sql_ui import conn, flagStatus, info_profile, updateProfile, updateHobbynspec, get_comboBox_list_career, \
    info_career
from model_functions import *


class CareerDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(CareerDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(12)

        if index.column() == 1:
            option.displayAlignment = QtCore.Qt.AlignCenter

    def createEditor(self, parent, option, index):
        if index.column() == 2:
            return super(CareerDelegate, self).createEditor(parent, option, index)


class ModelWindow(QtWidgets.QDialog):
    def __init__(self, v_model_key):
        super(ModelWindow, self).__init__()
        uic.loadUi("./model_info_window.ui", self)  # ui파알을 위젯에 할당할 때 loadUi
        self.select_key = v_model_key

        profile_data = info_profile(v_model_key)
        self.flag_status = flagStatus(self.select_key, 1)  # status[1: 점유중 0: 비점유중]

        if not self.flag_status:
            QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중입니다.\n변경 내용이 있을 수 있으니 해당 사용자 작업 종료 후 다시 창을 여십시오.\n조회만 가능합니다.")
        # model_data
        self.select_info_profile = [profile_data[0], copy.deepcopy(profile_data[0])]  # [data_original, data_change]
        self.select_info_profile_hobbynspec = profile_data[1]  # no update, only insert, delete
        self.select_info_career = info_career( self.select_key)

        # model_profile
        for edit_key in self.select_info_profile[0].keys():
            cur_lineEdit = getattr(self, "lineEdit_profile_" + edit_key)
            cur_lineEdit.setText(self.select_info_profile[0][edit_key])

            cur_btn = getattr(self, "btn_profile_" + edit_key)
            cur_btn.clicked.connect(lambda checked, p_edit_key=edit_key: self.profileUpdate(p_edit_key))

        # model_profile - hobbynspec
        for data in self.select_info_profile_hobbynspec:
            try:
                self.addListWidgetItem(self.list_hobbynspec, data[1])
            except Exception as e:
                print(e)
                print(data)

        self.btn_profile_hobbynspec.clicked.connect(lambda: self.profileUpdate("hobbynspec"))
        self.btn_profile_all_save.clicked.connect(lambda: self.profileUpdate(""))
        self.setStyleSheet("QLineEdit { font: 11px; }")

        self.mainGroupBoxStyle("profile")
        self.mainGroupBoxStyle("career")
        self.groupBox_career_insert.setStyleSheet("QGroupBox#groupBox_career_insert { border: None;}")

        # career
        try:
            self.comboBox_career_insert.addItems(get_comboBox_list_career()[0])
            comboStyleCss(self.comboBox_career_insert, "120")

            self.tableWidget_career.setColumnWidth(0, 70)
            self.tableWidget_career.setColumnWidth(1, 40)
            self.tableWidget_career.setColumnWidth(2, 125)
            self.tableWidget_career.setColumnWidth(3, 45)
            self.careerTableColCount = 3
            self.careerTable()

            self.tableWidget_career.horizontalHeader().setFont(QtGui.QFont("", 7))
            self.tableWidget_career.verticalHeader().setVisible(False)
            self.tableWidget_career.setWordWrap(False)
            self.tableWidget_career.setEditTriggers(QAbstractItemView.DoubleClicked)

            career_delegate = CareerDelegate(self.tableWidget_career)
            self.tableWidget_career.setItemDelegate(career_delegate)
        except Exception as e:
            print(e)

        self.show()

    def mainGroupBoxStyle(self, v_groupBox_name):
        cur_groupBox = getattr(self, "groupBox_" + v_groupBox_name)
        cur_groupBox.setStyleSheet("""
            QGroupBox#groupBox_"""+v_groupBox_name+""" { background-color: rgb(213, 211, 247); border: 1px solid rgb(138, 135, 154); }
        """)

    def profileUpdate(self, v_type):
        try:
            if self.flag_status:
                if v_type == "hobbynspec":
                    edit_text = self.lineEdit_profile_hobbynspec.text()
                    if len(edit_text):
                        if self.updateExec([True, "저장 완료", "저장 실패"], updateHobbynspec, self.select_key, "INSERT", edit_text):
                            conn.commit()
                            self.hobbynspecInsertList(edit_text)
                    else:
                        QMessageBox.about(self, "알림", "빈 값은 추가할 수 없습니다.")
                else:
                    original_data = self.select_info_profile[0]
                    for edit_key in original_data.keys():
                        if not v_type or edit_key == v_type :
                            cur_lineEdit = getattr(self, "lineEdit_profile_" + edit_key)
                            self.select_info_profile[1][edit_key] = cur_lineEdit.text()
                    change_data = self.select_info_profile[1]

                    update_items = []
                    for edit_key in change_data.keys():
                        if not v_type or edit_key == v_type:
                            if change_data[edit_key] != original_data[edit_key]:
                                update_items.append([edit_key, change_data[edit_key]])

                    if v_type:
                        if len(update_items):
                            if self.updateExec([True, "저장 완료", "저장 실패"], updateProfile, self.select_key, update_items):
                                for items in update_items:
                                    original_data[items[0]] = items[1]
                                conn.commit()
                        else:
                            QMessageBox.about(self, "알림", "변경된 데이터가 없습니다.")
                    else:  # profile all
                        if len(update_items):
                            profile_result = self.updateExec([False], updateProfile, self.select_key, update_items)
                            if profile_result:
                                for items in update_items:
                                    original_data[items[0]] = items[1]
                        else:
                            profile_result = 1

                        hobbynspec_input_text = self.lineEdit_profile_hobbynspec.text()
                        if hobbynspec_input_text:
                            hobbynspec_result = self.updateExec([False], updateHobbynspec, self.select_key, "INSERT",
                                               hobbynspec_input_text)
                            if hobbynspec_result:
                                self.hobbynspecInsertList(hobbynspec_input_text)
                        else:
                            hobbynspec_result = 1

                        if profile_result == 1 and hobbynspec_result == 1:
                            QMessageBox.about(self, "알림", "입력된 내용이 없습니다.")
                        elif profile_result and hobbynspec_result:
                            conn.commit()
                            QMessageBox.about(self, "알림", "일괄 저장되었습니다.")
                        else:
                            QMessageBox.about(self, "알림", "저장에 오류가 있습니다.")
            else:
                QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중이니 해당 사용자의 작업 종료 후 다시 창을 여십시오.")
        except Exception as e:
            print(e)

    def listItemDelete(self, v_type, v_del_row):
        try:
            if self.flag_status:
                if v_type == "hobbynspec":
                    if self.updateExec([True, "삭제 완료", "삭제 실패"], updateHobbynspec, self.select_key, "DELETE", str(v_del_row+1)):
                        conn.commit()
                        self.list_hobbynspec.takeItem(v_del_row)
                else:
                    QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중이니 해당 사용자의 작업 종료 후 다시 창을 여십시오.")
        except Exception as e:
            print(e)

    def updateExec(self, v_msg, fn_sql, *fn_param):
        msgBox = QMessageBox()
        if fn_sql(fn_param):
            v_msg[0] and msgBox.about(self, "알림", v_msg[1])
            return True
        else:
            v_msg[0] and msgBox.about(self, "알림", v_msg[2])
            return False

    def addListWidgetItem(self, v_list_widget, v_ins_data):
        listItem = QListWidgetItem()
        listItem.setText(v_ins_data)

        detailsFont = QtGui.QFont()
        detailsFont.setPixelSize(11)
        listItem.setFont(detailsFont)

        detailsFont = QtGui.QFont()
        detailsFont.setPointSize(10)

        cWidget = QWidget()
        cWidget.setStyleSheet("""
            background: transparent;
            border: 0px;
        """)
        layout = QBoxLayout(QBoxLayout.RightToLeft)
        layout.setContentsMargins(0, 0, 0, 0)
        layoutButton = QPushButton("X")
        layoutButton.setFixedSize(QtCore.QSize(18, 14))
        layoutButton.setStyleSheet(list_btn_style)
        layoutButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        layoutButton.clicked.connect(
            lambda:
            self.listItemDelete("hobbynspec", v_list_widget.currentRow())
            if v_list_widget.currentRow() > -1
            else QMessageBox.about(self, "알림", "선택된 항목이 없습니다.")
        )
        layout.addWidget(layoutButton, 0, QtCore.Qt.AlignRight)
        cWidget.setLayout(layout)
        v_list_widget.addItem(listItem)
        v_list_widget.setItemWidget(listItem, cWidget)

    def hobbynspecInsertList(self, v_insert_text):
        self.addListWidgetItem(self.list_hobbynspec, v_insert_text)
        original_data = self.select_info_profile_hobbynspec
        print(original_data)
        original_data.append([(original_data[-1][0]+1 if len(original_data) else 1), v_insert_text])
        print(original_data)
        self.lineEdit_profile_hobbynspec.setText("")

    def careerTable(self):
        if self.select_info_career:
            self.tableWidget_career.setRowCount(0)

            career_data = []
            for key_type in self.select_info_career.keys():
                career_type_data = self.select_info_career[key_type]
                for key_no in career_type_data.keys():
                    career_data.append([key_type, key_no, career_type_data[key_no]])

            for m_idx, m_row in enumerate(career_data):
                self.tableWidget_career.insertRow(m_idx)
                self.tableWidget_career.setRowHeight(m_idx, 15)
                for r_idx, r_data in enumerate(m_row):
                    cell_item = QTableWidgetItem(str(r_data if r_data else ""))
                    self.tableWidget_career.setItem(m_idx, r_idx, cell_item)

                cellWidget = QWidget()
                layoutCB = QHBoxLayout(cellWidget)
                btn_career_del = QPushButton("X")
                btn_career_del.setFixedSize(QtCore.QSize(18, 14))
                btn_career_del.setStyleSheet(career_btn_style)
                btn_career_del.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                btn_career_del.clicked.connect(lambda checked, p_row_no=m_idx: self.careerDelete(p_row_no))
                layoutCB.addWidget(btn_career_del)
                layoutCB.setAlignment(QtCore.Qt.AlignCenter)
                layoutCB.setContentsMargins(0, 0, 0, 0)
                cellWidget.setLayout(layoutCB)

                self.tableWidget_career.setCellWidget(m_idx, 3, cellWidget)
        else:
            self.tableWidget.setRowCount(1)
            self.tableWidget.setSpan(0, 0, 1, self.careerTableColCount)
            self.tableWidget.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
            self.tableWidget.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)

    def careerDelete(self, v_row_no):
        pass

    def closeEvent(self, event):
        if self.flag_status == 1:
            flagStatus(self.select_key, 0)


list_btn_style = """
    font-size: 10px;
    font-weight: bold;
    color: #6e6e6e;
    margin: 1px;
    border-radius: 3px;
    border: 1px solid #6e6e6e;
"""

career_btn_style = """
    font-size: 12px;
    font-weight: bold;
    color: #6e6e6e;
    border-radius: 3px;
    border: 1px solid #6e6e6e;
    padding-top: 1px;
"""

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModelWindow(278)
    app.exec_()
