import sys
import copy
import re
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *

from model_sql_ui import conn, flagStatus, info_profile, updateProfile, updateHobbynspec, get_comboBox_list_career, \
    info_career, updateCareer,getCMCodeList, info_contact, updateContact, getColType, getMaxKeyOfProfile, \
    info_contract, updateContract
from model_functions import *

flag_massage = "다른 사용자가 모델 데이터를 작업 중이니\n해당 사용자의 작업 종료 후 다시 창을 여십시오."
color_set = {
    "name": "#bf472c",  # changed or error
    "list": [191, 71, 44]
}


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

        if index.column() in [1,3,4,5,7,8]:
            option.displayAlignment = QtCore.Qt.AlignCenter

    def createEditor(self, parent, option, index):
        if index.column() in [2,4,5,6,7,8]:
            return super(ContactDelegate, self).createEditor(parent, option, index)


class ContractDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(ContractDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(10)

        if index.column() in [2,4,5]:
            option.displayAlignment = QtCore.Qt.AlignCenter
        elif index.column() in [3]:
            option.displayAlignment = QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter

    # def createEditor(self, parent, option, index):
    #     if index.column() in [2,4,5,6,7,8]:
    #         return super(ContractDelegate, self).createEditor(parent, option, index)


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
        self.contract_data_rng_idx = 4  # 데이터 포함 제한 index
        self.select_info_contract = []
        self.contract_table_cols = []

        self.combobox_idx_in_data = {
            "contact": [2],
            "contract": [1]
        }
        self.table_no_edit_column = {
            "contact": ["no"]
        }
        self.table_merge = {
            "contract": {"col": [1, 4]}
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

        # 영역 그룹박스 style #그룹박스 개체명 : 하위 위젯 상속 방지
        self.mainGroupBoxStyle("profile")
        self.mainGroupBoxStyle("career")
        self.mainGroupBoxStyle("contact")
        self.mainGroupBoxStyle("contract")
        # 항목별 그룹박스 border
        self.groupBox_career_type.setStyleSheet("QGroupBox#groupBox_career_type { border: None;}")
        self.groupBox_career_detail_gubun.setStyleSheet("QGroupBox#groupBox_career_detail_gubun { border: None;}")
        self.groupBox_career_careers.setStyleSheet("QGroupBox#groupBox_career_careers { border: None;}")
        self.groupBox_career_careers.setStyleSheet("QGroupBox#groupBox_career_careers { border: None;}")
        self.groupBox_contact_1.setStyleSheet("QGroupBox#groupBox_contact_1 { border: None;}")
        self.groupBox_contact_2.setStyleSheet("QGroupBox#groupBox_contact_2 { border: None;}")
        self.groupBox_contact_3.setStyleSheet("QGroupBox#groupBox_contact_3 { border: None;}")
        self.groupBox_contract_1.setStyleSheet("QGroupBox#groupBox_contract_1 { border: None;}")
        self.groupBox_contract_2.setStyleSheet("QGroupBox#groupBox_contract_2 { border: None;}")

        # career
        try:
            self.comboBox_career_type.addItems(get_comboBox_list_career()[0])
            comboStyleCss(self.comboBox_career_type, "120")

            self.lineEdit_career_detail_gubun.setPlaceholderText("해당없음")

            self.btn_career_insert.clicked.connect(lambda: self.careerDataExec("INSERT"))
            self.btn_career_update.clicked.connect(lambda: self.careerDataExec("UPDATE"))
            self.btn_career_delete.clicked.connect(lambda: self.careerDataExec("DELETE"))
            self.btn_career_all_delete.clicked.connect(lambda: self.careerDataExec("ALL_DELETE"))

            self.tableWidget_career.setColumnWidth(0, 25)
            self.tableWidget_career.setColumnWidth(1, 50)
            self.tableWidget_career.setColumnWidth(2, 50)
            self.tableWidget_career.setColumnWidth(3, 35)
            self.tableWidget_career.setColumnWidth(4, 95)
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
        self.lineEdit_contact_name.setPlaceholderText("필수 입력 항목")
        try:
            contact_gubun_cd_data = getCMCodeList("CONTACT_GUBUN")
            self.comboBox_contact_gubun_list = contact_gubun_cd_data[0]
            self.comboBox_contact_gubun.addItems(self.comboBox_contact_gubun_list)
            comboStyleCss(self.comboBox_contact_gubun, "100")
            self.comboBox_contact_gubun_map_data = contact_gubun_cd_data[1]

            self.btn_contact_insert.clicked.connect(lambda: self.contactDataExec("INSERT"))
            self.btn_contact_update.clicked.connect(lambda: self.contactDataExec("UPDATE"))
            self.btn_contact_delete.clicked.connect(lambda: self.contactDataExec("DELETE"))
            self.btn_contact_all_delete.clicked.connect(lambda: self.contactDataExec("ALL_DELETE"))

            self.tableWidget_contact.setColumnWidth(0, 30)
            self.tableWidget_contact.setColumnWidth(1, 35)
            self.tableWidget_contact.setColumnWidth(2, 100)
            self.tableWidget_contact.setColumnWidth(3, 73)
            self.tableWidget_contact.setColumnWidth(4, 60)
            self.tableWidget_contact.setColumnWidth(5, 65)
            self.tableWidget_contact.setColumnWidth(6, 90)
            self.tableWidget_contact.setColumnWidth(7, 100)
            self.tableWidget_contact.setColumnWidth(8, 65)
            self.contactTable()

            self.tableWidget_contact.horizontalHeader().setFont(QtGui.QFont("", 8))
            self.tableWidget_contact.verticalHeader().setVisible(False)
            self.tableWidget_contact.verticalHeader().setDefaultSectionSize(15)
            self.tableWidget_contact.setWordWrap(False)
            self.tableWidget_contact.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

            contact_delegate = ContactDelegate(self.tableWidget_contact)
            self.tableWidget_contact.setItemDelegate(contact_delegate)

            self.tableWidget_contact.itemChanged.connect(self.tableCellEdited)
        except Exception as e:
            QMessageBox.critical(self, "Error", e.args[0])
            self.close()

        # contract
        self.lineEdit_contract_type.setPlaceholderText("해당없음")
        self.lineEdit_contract_amount.setPlaceholderText("기준")
        try:
            contract_c_month_cd_data = getCMCodeList("C_MONTH")
            self.comboBox_contract_c_month_list = contract_c_month_cd_data[0]
            self.comboBox_contract_c_month.addItems(self.comboBox_contract_c_month_list)
            comboStyleCss(self.comboBox_contract_c_month, "100")
            self.comboBox_contract_c_month_map_data = contract_c_month_cd_data[1]

            self.btn_contract_insert.clicked.connect(lambda: self.contractDataExec("INSERT"))
            self.btn_contract_delete.clicked.connect(lambda: self.contractDataExec("DELETE"))
            self.btn_contract_all_delete.clicked.connect(lambda: self.contractDataExec("ALL_DELETE"))
    
            self.tableWidget_contract.setColumnWidth(0, 30)
            self.tableWidget_contract.setColumnWidth(1, 75)
            self.tableWidget_contract.setColumnWidth(2, 60)
            self.tableWidget_contract.setColumnWidth(3, 75)
            self.tableWidget_contract.setColumnWidth(4, 60)
            self.tableWidget_contract.setColumnWidth(5, 65)
            self.contractTable()
    
            self.tableWidget_contract.horizontalHeader().setFont(QtGui.QFont("", 8))
            self.tableWidget_contract.verticalHeader().setVisible(False)
            self.tableWidget_contract.verticalHeader().setDefaultSectionSize(15)
            self.tableWidget_contract.setWordWrap(False)
            self.tableWidget_contract.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
    
            contract_delegate = ContractDelegate(self.tableWidget_contract)
            self.tableWidget_contract.setItemDelegate(contract_delegate)
            self.tableWidget_contract.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        except Exception as e:
            QMessageBox.critical(self, "Error", e.args[0])
            self.close()

        # lineEdit value check
        self.column_type_data = getColType()

        # new : button set disabled
        if not self.select_key:
            for btn in self.findChildren(QPushButton):
                if btn.objectName() and btn.objectName() != "btn_profile_all_save":
                    btn.setDisabled(True)
            self.btn_profile_all_save.setText("등록")
            QMessageBox.about(self, "알림", "신규 모델 정보 등록\n- 추가 버튼 외 기타 버튼은 작동하지 않습니다.\n- 모델 프로필이 등록된 후 버튼이 활성화 됩니다.")
        self.show()

    def mainGroupBoxStyle(self, v_groupBox_name):
        cur_groupBox = getattr(self, "groupBox_" + v_groupBox_name)
        cur_groupBox.setStyleSheet("""
            QGroupBox#groupBox_"""+v_groupBox_name+""" { background-color: rgb(213, 211, 247); border: 1px solid rgb(138, 135, 154); }
        """)

    def profileUpdate(self, v_type):
        try:
            if self.flag_status:
                if self.btnExecOrCancel("save") == QMessageBox.Yes:
                    if v_type == "hobbynspec":
                        if self.column_value_type_check("profile", v_type):
                            edit_text = self.lineEdit_profile_hobbynspec.text()
                            if len(edit_text):
                                if self.updateExec([True, "저장 완료", "저장 실패"], updateHobbynspec, self.select_key, "INSERT", edit_text):
                                    conn.commit()
                                    self.hobbynspecInsertList(edit_text)
                            else:
                                QMessageBox.about(self, "알림", "빈 값은 추가할 수 없습니다.")
                    else:
                        if self.column_value_type_check("profile", v_type):
                            original_data = self.select_info_profile[0]

                            for edit_key in original_data.keys():
                                if not v_type or edit_key == v_type:
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
                                    profile_result = 0

                                hobbynspec_input_text = self.lineEdit_profile_hobbynspec.text()
                                if hobbynspec_input_text:
                                    hobbynspec_result = self.updateExec([False], updateHobbynspec, self.select_key, "INSERT",
                                                        hobbynspec_input_text)
                                    if hobbynspec_result:
                                        self.hobbynspecInsertList(hobbynspec_input_text)
                                else:
                                    hobbynspec_result = 0

                                if profile_result == 0 and hobbynspec_result == 0:
                                    QMessageBox.about(self, "알림", "입력된 내용이 없습니다.")
                                elif not self.select_key and profile_result:  # 신규 프로필 등록
                                    conn.commit()
                                    QMessageBox.about(self, "알림", "모델이 신규 생성되었습니다.")
                                    for btn in self.findChildren(QPushButton):
                                        if btn.objectName() and btn.objectName() != "btn_profile_all_save":
                                            btn.setEnabled(True)
                                    self.btn_profile_all_save.setText("일괄 반영")
                                    self.select_key = getMaxKeyOfProfile()
                                elif self.select_key and (profile_result or hobbynspec_result):
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
                    self.tableWidget_career.setCellWidget(m_idx, 0, self.tableCheckBox())

                    for r_idx, r_data in enumerate(m_row):
                        cell_item = QTableWidgetItem()
                        cell_item.setText(r_data if r_data else "")
                        self.tableWidget_career.setItem(m_idx, r_idx+1, cell_item)
                self.tableWidget_career.blockSignals(False)
                self.tableWidget_career.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                self.tableWidget_career.blockSignals(False)
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()
        else:
            try:
                self.tableWidget_career.blockSignals(True)
                self.tableWidget_career.setRowCount(0)
                self.tableWidget_career.insertRow(0)
                self.tableWidget_career.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
                self.tableWidget_career.setSpan(0, 0, 1, self.tableWidget_career.columnCount())
                self.tableWidget_career.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)
                self.tableWidget_career.blockSignals(False)
                self.tableWidget_career.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                self.tableWidget_career.blockSignals(False)
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()

    def careerDataExec(self, v_mod_type):
        data_list = []
        try:
            if self.flag_status:
                if v_mod_type == "INSERT":
                    careers_text = self.lineEdit_career_careers.text()
                    if careers_text:
                        if self.btnExecOrCancel("save") == QMessageBox.Yes:
                            if self.column_value_type_check("career"):
                                career_data = {"key": self.select_key,
                                               "career_type": self.comboBox_career_type.currentText(),
                                               "detail_gubun": nvl(self.lineEdit_career_detail_gubun.text(), self.lineEdit_career_detail_gubun.placeholderText()),
                                               "careers": careers_text}
                                data_list = [career_data]
                                if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateCareer, v_mod_type, data_list):
                                    conn.commit()
                                    self.careerTable()
                                self.lineEdit_career_careers.setText("")
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
                                print('committed')
                                self.careerTable()
                                print('reload')
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
                    self.tableWidget_contact.setCellWidget(m_idx, 0, self.tableCheckBox())

                    for r_idx, r_data in enumerate(m_row):
                        if r_idx in self.combobox_idx_in_data["contact"]:  # contact의 gubun[구분]
                            inComboBox = QComboBox()
                            inComboBox.addItems(self.comboBox_contact_gubun_list)
                            inComboBox.setCurrentText(r_data)
                            # inComboBox.setStyleSheet("""
                            #     QComboBox { font: 11px; }
                            #     QComboBox QAbstractItemView { font: 11px; min-width: 70px; }
                            #     QComboBox QAbstractItemView::item { font: 11px; min-height: 20px; }
                            # """)
                            self.tableWidget_contact.setCellWidget(m_idx, r_idx+1, inComboBox)
                        else:
                            cell_item = QTableWidgetItem()
                            cell_item.setText(str(r_data) if r_data else "")
                            self.tableWidget_contact.setItem(m_idx, r_idx + 1, cell_item)

                self.tableWidget_contact.blockSignals(False)
                self.tableWidget_contact.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()
        else:
            try:
                self.tableWidget_contact.blockSignals(True)
                self.tableWidget_contact.setRowCount(0)
                self.tableWidget_contact.insertRow(0)
                self.tableWidget_contact.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
                self.tableWidget_contact.setSpan(0, 0, 1, self.tableWidget_contact.columnCount())
                self.tableWidget_contact.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)
                self.tableWidget_contact.blockSignals(False)
                self.tableWidget_contact.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                self.tableWidget_contact.blockSignals(False)
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()

    def tableCellEdited(self, item):
        try:
            table_obj = item.tableWidget()
            table_obj_name = table_obj.objectName()
            table_item_obj = table_obj.item(item.row(), item.column())

            row_list = []
            for col_idx in range(table_obj.columnCount()):
                if col_idx > 0:
                    item_text = ""
                    table_col_item_obj = table_obj.item(item.row(), col_idx)
                    if table_col_item_obj is None:
                        table_widget_obj = table_obj.cellWidget(item.row(), col_idx)
                        if isinstance(table_widget_obj, QComboBox):
                            item_text = table_widget_obj.currentText()
                    else:
                        item_text = table_col_item_obj.text()

                    row_list.append(item_text)

            row_value_changed = False
            if table_obj_name == "tableWidget_career":
                original_text = self.select_info_career[row_list[0]][row_list[1]][row_list[2]]
                changed_text = item.text() if item.text() else None
                row_value_changed = False if original_text == changed_text else True
            elif table_obj_name == "tableWidget_contact":
                for idx, data in enumerate(self.select_info_contact[item.row()]):
                    data = "" if data is None else data
                    if not row_value_changed and data != row_list[idx]:
                        row_value_changed = True

            widget_checkBox = table_obj.cellWidget(item.row(), 0).findChild(QCheckBox)
            if row_value_changed:
                widget_checkBox.setChecked(True)
                if table_item_obj is not None:
                    table_item_obj.setForeground(QtGui.QBrush(QtGui.QColor(color_set["list"][0], color_set["list"][1], color_set["list"][2])))
            else:
                widget_checkBox.setChecked(False)
                if table_item_obj is not None:
                    table_item_obj.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
            self.close()
            
    def contactDataExec(self, v_mod_type):
        data_list = []
        try:
            if self.flag_status:
                if v_mod_type == "INSERT":
                    if self.btnExecOrCancel("save") == QMessageBox.Yes:
                        if self.column_value_type_check("contact"):
                            contact_data = {"key": self.select_key}
                            for col_idx, col in enumerate(self.contact_table_cols):
                                if col in self.table_no_edit_column["contact"]:
                                    pass
                                elif col_idx in self.combobox_idx_in_data["contact"]:
                                    contact_data[col] = self.comboBox_contact_gubun_map_data[self.comboBox_contact_gubun.currentText()]
                                else:
                                    contact_data[col] = getattr(self, "lineEdit_contact_"+col).text()

                            data_list = [contact_data]
                            if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateContact, v_mod_type, data_list):
                                conn.commit()
                                self.contactTable()
                            for col_idx, col in enumerate(self.contact_table_cols):
                                if col in self.table_no_edit_column["contact"]:
                                    pass
                                elif col_idx in self.combobox_idx_in_data["contact"]:
                                    self.comboBox_contact_gubun.setCurrentIndex(0)
                                else:
                                    getattr(self, "lineEdit_contact_"+col).setText("")
                elif v_mod_type == "ALL_DELETE":
                    if self.select_info_contact:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateContact, v_mod_type, [{"key": self.select_key}]):
                                conn.commit()
                                self.contactTable()
                    else:
                        QMessageBox.about(self, "알림", "삭제할 데이터가 없습니다.")
                else:  # UPDATE/DELETE
                    checked_list = getCheckListFromTable(self.tableWidget_contact, QCheckBox)
                    if checked_list:
                        if self.btnExecOrCancel("save" if v_mod_type == "UPDATE" else "del") == QMessageBox.Yes:
                            for chk_idx in checked_list:
                                contact_data = {"key": self.select_key}
                                if v_mod_type == "UPDATE":
                                    original_data = self.select_info_contact[chk_idx]
                                    changed_data = []
                                    for col_idx in list(range(self.tableWidget_contact.columnCount()))[1:]:
                                        if col_idx-1 in self.combobox_idx_in_data["contact"]:
                                            combo_text = self.tableWidget_contact.cellWidget(chk_idx, col_idx).currentText()
                                            changed_data.append(self.comboBox_contact_gubun_map_data[combo_text])
                                        else:
                                            table_item_data = self.tableWidget_contact.model().index(chk_idx, col_idx).data()
                                            changed_data.append(table_item_data if table_item_data else None)

                                    for idx, col in enumerate(self.contact_table_cols):
                                        if col in self.table_no_edit_column["contact"]:
                                            contact_data[self.contact_table_cols[idx]] = original_data[idx]
                                        elif original_data[idx] != changed_data[idx]:
                                            contact_data[self.contact_table_cols[idx]] = changed_data[idx]
                                    data_list.append(contact_data)
                                else:
                                    for idx, col in enumerate(self.contact_table_cols):
                                        if col == "no":
                                            contact_data["no"] = self.select_info_contact[chk_idx][idx]
                                    data_list.append(contact_data)
                            if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateContact, v_mod_type, data_list):
                                conn.commit()
                                self.contactTable()
                    else:
                        QMessageBox.about(self, "알림", "선택된 데이터가 없습니다.")
            else:
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
            
    def contractTable(self):
        contract_data = info_contract(self.select_key)
        if contract_data:
            self.contract_table_cols = contract_data[0]
            self.select_info_contract = contract_data[1]

        if self.select_info_contract:
            try:
                self.tableWidget_contract.blockSignals(True)
                self.tableWidget_contract.setRowCount(0)

                r_no_idx = self.contract_table_cols.index("r_no")
                merge_col_idx = self.contract_table_cols.index("merge_col_cnt")
                for m_idx, m_row in enumerate(self.select_info_contract):
                    self.tableWidget_contract.insertRow(m_idx)
                    self.tableWidget_contract.setCellWidget(m_idx, 0, self.tableCheckBox())

                    for r_idx, r_data in enumerate(m_row):
                        if r_idx <= self.contract_data_rng_idx:
                            cell_item = QTableWidgetItem()
                            cell_item.setText(str(r_data) if r_data else "")
                            self.tableWidget_contract.setItem(m_idx, r_idx + 1, cell_item)
                        if m_row[r_no_idx] == 1:
                            if r_idx in self.table_merge["contract"]["col"]:
                                self.tableWidget_contract.setSpan(m_idx, r_idx, m_row[merge_col_idx], 1)

                self.tableWidget_contract.blockSignals(False)
                self.tableWidget_contract.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()
        else:
            try:
                self.tableWidget_contract.blockSignals(True)
                self.tableWidget_contract.setRowCount(0)
                self.tableWidget_contract.insertRow(0)
                self.tableWidget_contract.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
                self.tableWidget_contract.setSpan(0, 0, 1, self.tableWidget_contract.columnCount())
                self.tableWidget_contract.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)
                self.tableWidget_contract.blockSignals(False)
                self.tableWidget_contract.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                self.tableWidget_contract.blockSignals(False)
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()

    def contractDataExec(self, v_mod_type):
        data_list = []
        try:
            if self.flag_status:
                if v_mod_type == "INSERT":
                    if self.btnExecOrCancel("save") == QMessageBox.Yes:
                        if self.column_value_type_check("contract"):
                            contract_data = {"key": self.select_key}
                            for col_idx, col in enumerate(self.contract_table_cols):
                                if col_idx in self.combobox_idx_in_data["contract"]:
                                    contract_data[col] = self.comboBox_contract_c_month_map_data[self.comboBox_contract_c_month.currentText()]
                                elif col == "type":
                                    contract_data[col] = nvl(self.lineEdit_contract_type.text(), self.lineEdit_contract_type.placeholderText())
                                else:
                                    try:
                                        contract_data[col] = getattr(self, "lineEdit_contract_"+col).text()
                                    except AttributeError:
                                        continue

                            data_list = [contract_data]
                            if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateContract, v_mod_type, data_list):
                                conn.commit()
                                self.contractTable()
                            for col_idx, col in enumerate(self.contract_table_cols):
                                if col_idx in self.combobox_idx_in_data["contract"]:
                                    self.comboBox_contract_c_month.setCurrentIndex(0)
                                else:
                                    try:
                                        getattr(self, "lineEdit_contract_"+col).setText("")
                                    except AttributeError:
                                        continue

                elif v_mod_type == "ALL_DELETE":
                    if self.select_info_contract:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateContract, v_mod_type, [{"key": self.select_key}]):
                                conn.commit()
                                self.contractTable()
                    else:
                        QMessageBox.about(self, "알림", "삭제할 데이터가 없습니다.")
                else:  # DELETE
                    checked_list = getCheckListFromTable(self.tableWidget_contract, QCheckBox)
                    if checked_list:
                        if self.btnExecOrCancel("save" if v_mod_type == "UPDATE" else "del") == QMessageBox.Yes:
                            for chk_idx in checked_list:
                                contract_data = {"key": self.select_key}
                                if v_mod_type == "DELETE":
                                    for idx, col in enumerate(self.contract_table_cols):
                                        if col == "type":
                                            contract_data[col] = self.select_info_contract[chk_idx][idx]
                                        elif col == "c_month":
                                            contract_data[col] = self.comboBox_contract_c_month_map_data[self.comboBox_contract_c_month.currentText()]
                                    data_list.append(contract_data)

                            if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateContract, v_mod_type, data_list):
                                conn.commit()
                                self.contractTable()
                    else:
                        QMessageBox.about(self, "알림", "선택된 데이터가 없습니다.")
            else:
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])

    def btnExecOrCancel(self, v_exec_type):
        question_msg_text = {"save": "저장", "del": "삭제"}
        reply = QMessageBox.question(self, " ", question_msg_text[v_exec_type] + "하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No)
        return reply

    def column_value_type_check(self, v_type_gubun, v_column=None):
        key_column_input_check = True
        message_list = []
        for data in self.column_type_data[v_type_gubun]:
            if not v_column or data[0] == v_column:
                obj_lineEdit = getattr(self, "lineEdit_" + v_type_gubun + "_" + data[0])
                lineEdit_input_text = obj_lineEdit.text()

                check_value_type = "str"
                try:
                    float(lineEdit_input_text)
                    check_value_type = "float"
                except ValueError:
                    pass
                try:
                    int(lineEdit_input_text)
                    check_value_type = "int"
                except ValueError:
                    pass

                object_item_name = "amount" if v_type_gubun == "contract" and data[0] == "amount2" else data[0]
                obj_label = getattr(self, "label_" + v_type_gubun + "_" + object_item_name)
                label_text = QtGui.QTextDocumentFragment.fromHtml(obj_label.text()).toPlainText()

                if data[0] == "name" and len(lineEdit_input_text.replace(" ", "")) <= 1:
                    key_column_input_check = False
                    message_list.append(label_text.replace(" ", "") + "(은)는 필수 입력 항목입니다.")
                    break

                if check_value_type == data[1]:
                    if data[2] is not None:
                        if check_value_type == "float":
                            string_length = data[2].split(",")
                            divided_text = re.findall("[0-9]+", lineEdit_input_text)
                            if len(divided_text[0]) > int(string_length[0]):
                                message_list.append([obj_lineEdit, label_text.replace(" ", "") + "의 입력된 값이 정수 부분 제한 자리수보다 큰 값을 입력하였습니다."])
                            elif len(divided_text[1]) > int(string_length[1]):
                                message_list.append([obj_lineEdit, label_text.replace(" ", "") + "의 입력된 값이 소수점 부분 제한 자리수보다 큰 값을 입력하였습니다."])
                        elif len(lineEdit_input_text) > int(data[2]):
                            message_list.append([obj_lineEdit, label_text.replace(" ", "") + "의 입력된 값이 제한된 길이를 초과하였습니다."])
                    else:
                        pass
                elif data[1] == "int" and check_value_type == "float":
                    message_list.append([obj_lineEdit, label_text.replace(" ", "") + "에는 소수점이 허락되지 않습니다."])
                elif not lineEdit_input_text or data[1] == "str" or (data[1] == "float" and check_value_type == "int"):
                    pass
                else:
                    message_list.append([obj_lineEdit, label_text.replace(" ", "") + "에 입력된 값이 맞게 입력되었는지 확인하세요."])

        if not key_column_input_check:
            QMessageBox.about(self, "알림", message_list[0])
        elif message_list:
            msg_text = ""
            for idx, msg in enumerate(message_list):
                msg_text += msg[1] + ("" if idx == len(message_list)-1 else "\n")
                msg[0].setStyleSheet("color: " + color_set["name"])
            QMessageBox.about(self, "알림", msg_text)
        else:
            for data in self.column_type_data[v_type_gubun]:
                if not v_column or data[0] == v_column:
                    obj_lineEdit = getattr(self, "lineEdit_" + v_type_gubun + "_" + data[0])
                    if obj_lineEdit.palette().windowText().color().name() == color_set["name"]:
                        obj_lineEdit.setStyleSheet("color: #000000")
            return True

    def tableCheckBox(self):
        cellWidget = QWidget()
        layoutCB = QHBoxLayout(cellWidget)
        checkBox = QCheckBox()
        layoutCB.addWidget(checkBox)
        layoutCB.setAlignment(QtCore.Qt.AlignCenter)
        layoutCB.setContentsMargins(0, 0, 0, 0)
        cellWidget.setLayout(layoutCB)

        return cellWidget

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            pass

    def closeEvent(self, event):
        if self.select_key and self.flag_status == 1:
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

button_disabled = """
    QPushButton:disabled {
        background-color: #eee;
    }
"""

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModelWindow(521)
    app.exec_()