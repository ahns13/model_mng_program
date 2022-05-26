import sys
import copy
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *

from model_sql_ui import conn, flagStatus, info_profile, updateProfile, updateHobbynspec, get_comboBox_list_career, \
    info_career, updateCareer,getCMCodeList, info_contact
from model_functions import *

flag_massage = "다른 사용자가 모델 데이터를 작업 중이니\n해당 사용자의 작업 종료 후 다시 창을 여십시오."


class CareerDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(CareerDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(10)

        if index.column() == 3:
            option.displayAlignment = QtCore.Qt.AlignCenter

    def createEditor(self, parent, option, index):
        if index.column() == 4:
            return super(CareerDelegate, self).createEditor(parent, option, index)


class ContactDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(ContactDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(10)

        if index.column() in [2,3,4,5,7]:
            option.displayAlignment = QtCore.Qt.AlignCenter

    def createEditor(self, parent, option, index):
        if index.column() in [1,3,4,5,6,7]:
            return super(ContactDelegate, self).createEditor(parent, option, index)


class ModelWindow(QtWidgets.QDialog):
    def __init__(self, v_model_key=""):
        super(ModelWindow, self).__init__()
        uic.loadUi("./model_info_window.ui", self)  # ui파알을 위젯에 할당할 때 loadUi
        self.select_key = v_model_key

        profile_data = info_profile(v_model_key)
        # flag_status[1: 점유중 0: 비점유중]
        self.flag_status = flagStatus(self.select_key, 1) if self.select_key else 1

        if not self.flag_status:
            QMessageBox.about(self, "알림", flag_massage + "\n조회만 가능합니다.")
        # model_data
        self.select_info_profile = [profile_data[0], copy.deepcopy(profile_data[0])]  # [data_original, data_change]
        self.select_info_profile_hobbynspec = profile_data[1]  # no update, only insert, delete
        self.select_info_career = {}
        self.career_table_cols = []
        self.select_info_contact = []
        self.contact_table_cols = []
        self.career_table_data_rng = {
            # start_col_index, col_count
            "UPDATE": range(1, 5),
            "DELETE": range(1, 4)
        }

        # model_profile
        self.lineEdit_profile_name.setPlaceholderText("필수 입력 항목")
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

        # 그룹박스 스타일: 하위 상속 방지 - #개체명 표시
        self.mainGroupBoxStyle("profile")
        self.mainGroupBoxStyle("career")
        self.mainGroupBoxStyle("contact")
        # 그룹박스 border
        self.groupBox_career_type.setStyleSheet("QGroupBox#groupBox_career_type { border: None;}")
        self.groupBox_career_detail_gubun.setStyleSheet("QGroupBox#groupBox_career_detail_gubun { border: None;}")
        self.groupBox_career_insert_item.setStyleSheet("QGroupBox#groupBox_career_insert_item { border: None;}")
        self.groupBox_contact_1.setStyleSheet("QGroupBox#groupBox_contact_1 { border: None;}")
        self.groupBox_contact_2.setStyleSheet("QGroupBox#groupBox_contact_2 { border: None;}")
        self.groupBox_contact_3.setStyleSheet("QGroupBox#groupBox_contact_3 { border: None;}")

        # career
        try:
            self.comboBox_career_type.addItems(get_comboBox_list_career()[0])
            comboStyleCss(self.comboBox_career_type, "120")

            self.lineEdit_career_detail_gubun.setPlaceholderText("해당없음")

            self.btn_career_insert.clicked.connect(lambda: self.careerDataExec("INSERT"))
            self.btn_career_update.clicked.connect(lambda: self.careerDataExec("UPDATE"))
            self.btn_career_delete.clicked.connect(lambda: self.careerDataExec("DELETE"))
            self.btn_career_all_delete.clicked.connect(lambda: self.careerDataExec("ALL_DELETE"))

            self.tableWidget_career.setColumnWidth(0, 27)
            self.tableWidget_career.setColumnWidth(1, 63)
            self.tableWidget_career.setColumnWidth(2, 55)
            self.tableWidget_career.setColumnWidth(3, 35)
            self.tableWidget_career.setColumnWidth(4, 110)
            self.careerTable()

            self.tableWidget_career.horizontalHeader().setFont(QtGui.QFont("", 8))
            self.tableWidget_career.verticalHeader().setVisible(False)
            self.tableWidget_career.verticalHeader().setDefaultSectionSize(15)
            self.tableWidget_career.setWordWrap(False)
            self.tableWidget_career.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

            career_delegate = CareerDelegate(self.tableWidget_career)
            self.tableWidget_career.setItemDelegate(career_delegate)

            self.tableWidget_career.itemChanged.connect(self.tableCellEdited)
        except Exception as e:
            QMessageBox.critical(self, "Error", e.args[0])
            self.close()

        # contact
        try:
            contact_gubun_cd_data = getCMCodeList("CONTACT_GUBUN")
            self.comboBox_contact_gubun_list = contact_gubun_cd_data[0]
            self.comboBox_contact_gubun.addItems(self.comboBox_contact_gubun_list)
            comboStyleCss(self.comboBox_contact_gubun, "100")
            self.comboBox_contact_gubun_map_data = contact_gubun_cd_data[1]

            # self.btn_contact_insert.clicked.connect(lambda: self.contactDataExec("INSERT"))
            # self.btn_contact_update.clicked.connect(lambda: self.contactDataExec("UPDATE"))
            # self.btn_contact_delete.clicked.connect(lambda: self.contactDataExec("DELETE"))
            # self.btn_contact_all_delete.clicked.connect(lambda: self.contactDataExec("ALL_DELETE"))

            self.tableWidget_contact.setColumnWidth(0, 30)
            self.tableWidget_contact.setColumnWidth(1, 100)
            self.tableWidget_contact.setColumnWidth(2, 73)
            self.tableWidget_contact.setColumnWidth(3, 60)
            self.tableWidget_contact.setColumnWidth(4, 65)
            self.tableWidget_contact.setColumnWidth(5, 100)
            self.tableWidget_contact.setColumnWidth(6, 100)
            self.tableWidget_contact.setColumnWidth(7, 70)
            self.contactTable()

            self.tableWidget_contact.horizontalHeader().setFont(QtGui.QFont("", 8))
            self.tableWidget_contact.verticalHeader().setDefaultSectionSize(15)
            self.tableWidget_contact.setWordWrap(False)
            self.tableWidget_contact.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

            contact_delegate = ContactDelegate(self.tableWidget_contact)
            self.tableWidget_contact.setItemDelegate(contact_delegate)

            self.tableWidget_contact.itemChanged.connect(self.tableCellEdited)
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
                    if self.btnExecOrCancel("save") == QMessageBox.Yes:
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

                    name_check = len(self.lineEdit_profile_name.text().replace(" ", ""))
                    if (v_type == "name" or not v_type) and name_check <= 1:
                        QMessageBox.warning(self, "알림", "모델명에 값이 없거나\n입력된 값이 정확한지 확인해 주세요.")
                    elif v_type:
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
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
            self.close()

    def listItemDelete(self, v_type, v_del_row):
        if self.flag_status:
            if self.btnExecOrCancel("del") == QMessageBox.Yes:
                if v_type == "hobbynspec":
                    if self.updateExec([True, "삭제 완료", "삭제 실패"], updateHobbynspec, self.select_key, "DELETE", str(v_del_row+1)):
                        conn.commit()
                        self.list_hobbynspec.takeItem(v_del_row)
        else:
            QMessageBox.about(self, "알림", flag_massage)

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
            else QMessageBox.about(self, "알림", "선택된 항목이 없습니다.\n목록 중에 삭제할 데이터를 선택하세요.")
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

        if self.select_info_career:
            try:
                self.tableWidget_career.blockSignals(True)
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

                    cellWidget = QWidget()
                    layoutCB = QHBoxLayout(cellWidget)
                    chk_career_del = QCheckBox()
                    layoutCB.addWidget(chk_career_del)
                    layoutCB.setAlignment(QtCore.Qt.AlignCenter)
                    layoutCB.setContentsMargins(0, 0, 0, 0)
                    cellWidget.setLayout(layoutCB)
                    self.tableWidget_career.setCellWidget(m_idx, 0, cellWidget)

                    for r_idx, r_data in enumerate(m_row):
                        cell_item = QTableWidgetItem()
                        cell_item.setText(r_data if r_data else "")
                        self.tableWidget_career.setItem(m_idx, r_idx+1, cell_item)
                self.tableWidget_career.blockSignals(False)
                self.tableWidget_career.verticalHeader().setMinimumSectionSize(25)
            except Exception as e:
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()
        else:
            self.tableWidget_career.setRowCount(1)
            self.tableWidget_career.setSpan(0, 0, 1, self.tableWidget_career.columnCount())
            self.tableWidget_career.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
            self.tableWidget_career.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)

    def careerDataExec(self, v_mod_type):
        data_list = []
        try:
            if self.flag_status:
                if v_mod_type == "INSERT":
                    careers_text = self.lineEdit_career_insert_item.text()
                    if careers_text:
                        if self.btnExecOrCancel("save") == QMessageBox.Yes:
                            career_data = {"key": self.select_key,
                                           "career_type": self.comboBox_career_type.currentText(),
                                           "detail_gubun": nvl(self.lineEdit_career_detail_gubun.text(), self.lineEdit_career_detail_gubun.placeholderText()),
                                           "careers": careers_text}
                            data_list = [career_data]
                            if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateCareer, v_mod_type, data_list):
                                conn.commit()
                                self.careerTable()
                            self.lineEdit_career_insert_item.setText("")
                    else:
                        QMessageBox.about(self, "알림", "경력에 추가할 값을 입력하세요.")
                elif v_mod_type == "ALL_DELETE":
                    if self.select_info_career:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateCareer, v_mod_type, [{"key": self.select_key}]):
                                conn.commit()
                                self.careerTable()
                    else:
                        QMessageBox.about(self, "알림", "삭제할 데이터가 없습니다.")
                else:  # UPDATE/DELETE
                    checked_list = getCheckListFromTable(self.tableWidget_career, QCheckBox)
                    if checked_list:
                        if self.btnExecOrCancel("save" if v_mod_type == "UPDATE" else "del") == QMessageBox.Yes:
                            for chk_idx in checked_list:
                                career_data = {"key": self.select_key}
                                for col_index in self.career_table_data_rng[v_mod_type]:
                                    career_data[self.career_table_cols[col_index-1]] = self.tableWidget_career.model().index(chk_idx, col_index).data()
                                    data_list.append(career_data)
                            if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateCareer, v_mod_type, data_list):
                                conn.commit()
                                self.careerTable()
                    else:
                        QMessageBox.about(self, "알림", "선택된 데이터가 없습니다.")
            else:
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
            
    def contactTable(self):
        contact_data = info_contact(self.select_key)
        if contact_data:
            self.contact_table_cols = contact_data[0]
            self.select_info_contact = contact_data[1]

        if self.select_info_contact:
            try:
                self.tableWidget_contact.blockSignals(True)
                self.tableWidget_contact.setRowCount(0)

                for m_idx, m_row in enumerate(self.select_info_contact):
                    self.tableWidget_contact.insertRow(m_idx)

                    cellWidget = QWidget()
                    layoutCB = QHBoxLayout(cellWidget)
                    chk_contact_del = QCheckBox()
                    layoutCB.addWidget(chk_contact_del)
                    layoutCB.setAlignment(QtCore.Qt.AlignCenter)
                    layoutCB.setContentsMargins(0, 0, 0, 0)
                    cellWidget.setLayout(layoutCB)
                    self.tableWidget_contact.setCellWidget(m_idx, 0, cellWidget)

                    for r_idx, r_data in enumerate(m_row):
                        if r_idx == 1:  # contact의 gubun[구분]
                            inComboBox = QComboBox()
                            inComboBox.addItems(self.comboBox_contact_gubun_list)
                            inComboBox.setCurrentText(r_data)
                            inComboBox.setStyleSheet("""
                                QComboBox { font: 11px; }
                                QComboBox QAbstractItemView { font: 11px; min-width: 70px; }
                                QComboBox QAbstractItemView::item { font: 11px; min-height: 20px; }
                            """)
                            self.tableWidget_contact.setCellWidget(m_idx, r_idx+1, inComboBox)
                        else:
                            cell_item = QTableWidgetItem()
                            cell_item.setText(r_data if r_data else "")
                            self.tableWidget_contact.setItem(m_idx, r_idx + 1, cell_item)

                self.tableWidget_contact.blockSignals(False)
                self.tableWidget_contact.verticalHeader().setMinimumSectionSize(25)
            except Exception as e:
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()
        else:
            self.tableWidget_contact.setRowCount(1)
            self.tableWidget_contact.setSpan(0, 0, 1, self.tableWidget_contact.columnCount())
            self.tableWidget_contact.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
            self.tableWidget_contact.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)

    def tableCellEdited(self, item):
        try:
            table_obj = item.tableWidget()
            table_obj_name = table_obj.objectName()
            row_list = []
            for col_idx in range(table_obj.columnCount()):
                if col_idx > 0:
                    row_list.append(table_obj.item(item.row(), col_idx).text())

            original_text = ""
            if table_obj_name == "tableWidget_career":
                original_text = self.select_info_career[row_list[0]][row_list[1]][row_list[2]]
            elif table_obj_name == "tableWidget_contact":
                original_text = self.select_info_contact[item.row()][item.column()]

            changed_text = item.text()
            widget_checkBox = table_obj.cellWidget(item.row(), 0).findChild(QCheckBox)
            if original_text == changed_text:
                widget_checkBox.setChecked(False)
            else:
                widget_checkBox.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
            self.close()

    def btnExecOrCancel(self, v_exec_type):
        question_msg_text = {"save": "저장", "del": "삭제"}
        reply = QMessageBox.question(self, " ", question_msg_text[v_exec_type] + "하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No)
        return reply

    # def keyPressEvent(self, event):
    #     print(dir(self))
    #     try:
    #         if event.key() == QtCore.Qt.Key_F2:
    #             focusWidget = self.focusWidget()
    #             if isinstance(focusWidget, QTableWidget):
    #                 self.tableCellEdited()
    #     except Exception as e:
    #         print(e)

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
    window = ModelWindow(1)
    app.exec_()
