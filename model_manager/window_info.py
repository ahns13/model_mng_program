import sys
import copy
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *

from model_sql_ui import conn, flagStatus, info_profile, updateProfile, updateHobbynspec, get_comboBox_list_career, \
    info_career, updateCareer
from model_functions import *


class CareerDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(CareerDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(12)

        if index.column() == 3:
            option.displayAlignment = QtCore.Qt.AlignCenter

    def createEditor(self, parent, option, index):
        if index.column() == 4:
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
        self.select_info_career = {}
        self.career_table_cols = []
        self.career_table_data_rng = {
            # start_col_index, col_count
            "UPDATE": range(1,5),
            "DELETE": range(1,4)
        }

        # model_profile
        for edit_key in self.select_info_profile[0].keys():
            cur_lineEdit = getattr(self, "lineEdit_profile_" + edit_key)
            cur_lineEdit.setText(self.select_info_profile[0][edit_key])

            cur_btn = getattr(self, "btn_profile_" + edit_key)
            cur_btn.clicked.connect(lambda checked, p_edit_key=edit_key: self.profileUpdate(p_edit_key))

        # model_profile - hobbynspec
        for data in self.select_info_profile_hobbynspec:
            self.addListWidgetItem(self.list_hobbynspec, data[1])

        self.btn_profile_hobbynspec.clicked.connect(lambda: self.profileUpdate("hobbynspec"))
        self.btn_profile_all_save.clicked.connect(lambda: self.profileUpdate(""))
        self.setStyleSheet("QLineEdit { font: 11px; }")

        self.mainGroupBoxStyle("profile")
        self.mainGroupBoxStyle("career")
        self.groupBox_career_type.setStyleSheet("QGroupBox#groupBox_career_type { border: None;}")
        self.groupBox_career_detail_gubun.setStyleSheet("QGroupBox#groupBox_career_detail_gubun { border: None;}")
        self.groupBox_career_insert_item.setStyleSheet("QGroupBox#groupBox_career_insert_item { border: None;}")

        # career
        try:
            self.comboBox_career_type.addItems(get_comboBox_list_career()[0])
            comboStyleCss(self.comboBox_career_type, "120")

            self.lineEdit_career_detail_gubun.setPlaceholderText("해당없음")

            self.btn_career_insert.clicked.connect(lambda: self.careerDataExec("INSERT"))
            self.btn_career_update.clicked.connect(lambda: self.careerDataExec("UPDATE"))
            self.btn_career_delete.clicked.connect(lambda: self.careerDataExec("DELETE"))

            self.tableWidget_career.setColumnWidth(0, 30)
            self.tableWidget_career.setColumnWidth(1, 65)
            self.tableWidget_career.setColumnWidth(2, 70)
            self.tableWidget_career.setColumnWidth(3, 40)
            self.tableWidget_career.setColumnWidth(4, 120)
            self.careerTableColCount = 3
            self.careerTable()

            self.tableWidget_career.horizontalHeader().setFont(QtGui.QFont("", 7))
            self.tableWidget_career.verticalHeader().setVisible(False)
            self.tableWidget_career.setWordWrap(False)
            self.tableWidget_career.setEditTriggers(QAbstractItemView.DoubleClicked)

            career_delegate = CareerDelegate(self.tableWidget_career)
            self.tableWidget_career.setItemDelegate(career_delegate)
            self.tableWidget_career.itemChanged.connect(self.tableCellEdited)
        except Exception as e:
            QMessageBox.critical(self, "Error", e.args[0])
            self.close()

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
            QMessageBox.critical(self, "오류", e.args[0])
            self.close()

    def listItemDelete(self, v_type, v_del_row):
        if self.flag_status:
            if v_type == "hobbynspec":
                if self.updateExec([True, "삭제 완료", "삭제 실패"], updateHobbynspec, self.select_key, "DELETE", str(v_del_row+1)):
                    conn.commit()
                    self.list_hobbynspec.takeItem(v_del_row)
            else:
                QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중이니 해당 사용자의 작업 종료 후 다시 창을 여십시오.")

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
        original_data.append([(original_data[-1][0]+1 if len(original_data) else 1), v_insert_text])
        self.lineEdit_profile_hobbynspec.setText("")

    def careerTable(self):
        career_data = info_career(self.select_key)

        if career_data:
            self.career_table_cols = career_data[0]
            self.select_info_career = career_data[1]
            self.tableWidget_career.setRowCount(0)

            career_data_mod = []
            for key_type in self.select_info_career.keys():
                career_type_data = self.select_info_career[key_type]
                for key_detail in career_type_data.keys():
                    career_detail_data = career_type_data[key_detail]
                    for key_no in career_detail_data.keys():
                        career_data_mod.append([key_type, key_detail, key_no, career_detail_data[key_no]])

            for m_idx, m_row in enumerate(career_data_mod):
                self.tableWidget_career.insertRow(m_idx)
                self.tableWidget_career.setRowHeight(m_idx, 15)
                for r_idx, r_data in enumerate(m_row):
                    cell_item = QTableWidgetItem(str(r_data if r_data else ""))
                    self.tableWidget_career.setItem(m_idx, r_idx+1, cell_item)

                cellWidget = QWidget()
                layoutCB = QHBoxLayout(cellWidget)
                chk_career_del = QCheckBox()
                layoutCB.addWidget(chk_career_del)
                layoutCB.setAlignment(QtCore.Qt.AlignCenter)
                layoutCB.setContentsMargins(0, 0, 0, 0)
                cellWidget.setLayout(layoutCB)

                self.tableWidget_career.setCellWidget(m_idx, 0, cellWidget)
        else:
            self.tableWidget_career.setRowCount(1)
            self.tableWidget_career.setSpan(0, 0, 1, self.careerTableColCount)
            self.tableWidget_career.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
            self.tableWidget_career.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)

    def careerDataExec(self, v_mod_type):
        data_list = []
        try:
            if v_mod_type == "INSERT":
                career_data = {"key": self.select_key,
                               "career_type": self.comboBox_career_type.currentText(),
                               "detail_gubun": nvl(self.lineEdit_career_detail_gubun.text(), self.lineEdit_career_detail_gubun.placeholderText()),
                               "careers": self.lineEdit_career_insert_item.text()}
                data_list = [career_data]
                if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateCareer, v_mod_type, data_list):
                    conn.commit()
                    self.careerTable()
            elif v_mod_type == "ALL_DELETE":
                if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateCareer, v_mod_type, [{"key": self.select_key}]):
                    conn.commit()
                    self.careerTable()
            else:  # UPDATE/DELETE
                for chk_idx in getCheckListFromTable(self.tableWidget_career, QCheckBox):
                    career_data = {"key": self.select_key}
                    for col_index in self.career_table_data_rng[v_mod_type]:
                        career_data[self.career_table_cols[col_index-1]] = self.tableWidget_career.model().index(chk_idx, col_index).data()
                        data_list.append(career_data)
                if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateCareer, v_mod_type, data_list):
                    conn.commit()
                    self.careerTable()
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])

    def tableCellEdited(self, item):
        try:
            row_list = []
            for col_idx in range(self.tableWidget_career.columnCount()):
                if col_idx > 0:
                    row_list.append(self.tableWidget_career.item(item.row(), col_idx).text())
            original_text = self.select_info_career[row_list[0]][row_list[1]][row_list[2]]
            changed_text = item.text()
            widget_checkBox = self.tableWidget_career.cellWidget(item.row(), 0).findChild(QCheckBox)
            if original_text == changed_text:
                widget_checkBox.setChecked(False)
            else:
                widget_checkBox.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
            self.close()

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
