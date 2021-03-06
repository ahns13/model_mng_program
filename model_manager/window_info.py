import sys
import copy
import re
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *

from model_sql_ui import conn, flagStatus, info_profile, updateProfile, updateHobbynspec, get_comboBox_list_career, \
    info_career, updateCareer,getCMCodeList, info_contact, updateContact, getColType, getMaxKeyOfProfile, \
    info_contract, updateContract, info_other, updateOther
from model_functions import *
import model_images_rc


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


class OtherDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(OtherDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(10)

        if index.column() in [1,3]:
            option.displayAlignment = QtCore.Qt.AlignCenter

    def createEditor(self, parent, option, index):
        if index.column() in [2,3]:
            return super(OtherDelegate, self).createEditor(parent, option, index)
        

class ModelWindow(QtWidgets.QDialog):
    def __init__(self, v_login_user_name, v_model_key=""):
        super(ModelWindow, self).__init__()
        uic.loadUi("./model_info_window.ui", self)  # ui파알을 위젯에 할당할 때 loadUi
        self.login_user_name = v_login_user_name
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
        self.contract_update_org_data = [{}, {}]  # other, ap

        self.select_info_other = []
        self.other_table_cols = []
        
        self.lineEdit_disable_col = {
            "contract": ["type", "c_month"]
        }

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
        self.mainGroupBoxStyle("other")
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
        self.groupBox_other_info.setStyleSheet("QGroupBox#groupBox_other_info { border: None;}")

        # career
        try:
            self.comboBox_career_type.addItems(get_comboBox_list_career()[0])
            comboStyleCss(self.comboBox_career_type, "120")

            self.btn_career_insert.clicked.connect(lambda: self.careerDataExec("INSERT"))
            self.btn_career_update.clicked.connect(lambda: self.careerDataExec("UPDATE"))
            self.btn_career_delete.clicked.connect(lambda: self.careerDataExec("DELETE"))
            self.btn_career_all_delete.clicked.connect(lambda: self.careerDataExec("ALL_DELETE"))

            self.tableWidget_career.setColumnWidth(0, 25)
            self.tableWidget_career.setColumnWidth(1, 65)
            self.tableWidget_career.setColumnWidth(2, 50)
            self.tableWidget_career.setColumnWidth(3, 35)
            self.tableWidget_career.setColumnWidth(4, 95)
            self.tableDataCreater("career")

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
            self.tableDataCreater("contact")

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
        self.contract_table_selected_index = None
        try:
            contract_c_month_cd_data = getCMCodeList("C_MONTH")
            self.comboBox_contract_c_month_list = contract_c_month_cd_data[0]
            self.comboBox_contract_c_month.addItems(self.comboBox_contract_c_month_list)
            comboStyleCss(self.comboBox_contract_c_month, "100")
            self.comboBox_contract_c_month_map_data = contract_c_month_cd_data[1]

            self.btn_contract_insert.clicked.connect(lambda: self.contractDataExec("INSERT"))
            self.btn_contract_display.clicked.connect(lambda: self.contractDataExec("DISPLAY"))
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

        # other
        self.lineEdit_other_info.setPlaceholderText("필수 입력 항목")
        try:
            self.btn_other_insert.clicked.connect(lambda: self.otherDataExec("INSERT"))
            self.btn_other_update.clicked.connect(lambda: self.otherDataExec("UPDATE"))
            self.btn_other_delete.clicked.connect(lambda: self.otherDataExec("DELETE"))
            self.btn_other_all_delete.clicked.connect(lambda: self.otherDataExec("ALL_DELETE"))

            self.tableWidget_other.setColumnWidth(0, 30)
            self.tableWidget_other.setColumnWidth(1, 35)
            self.tableWidget_other.setColumnWidth(2, 130)
            self.tableWidget_other.setColumnWidth(3, 60)
            self.tableDataCreater("other")

            self.tableWidget_other.horizontalHeader().setFont(QtGui.QFont("", 8))
            self.tableWidget_other.verticalHeader().setVisible(False)
            self.tableWidget_other.verticalHeader().setDefaultSectionSize(15)
            self.tableWidget_other.setWordWrap(False)
            self.tableWidget_other.setEditTriggers(
                QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

            other_delegate = OtherDelegate(self.tableWidget_other)
            self.tableWidget_other.setItemDelegate(other_delegate)

            self.tableWidget_other.itemChanged.connect(self.tableCellEdited)
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

        # init button
        self.buttonRefresh("profile")
        self.buttonRefresh("contact")
        self.buttonRefresh("contract")
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
                                if self.updateExec([True, "저장 완료", "저장 실패"], updateHobbynspec, "INSERT",
                                                   {"key": self.select_key, "user_name": self.login_user_name, "value": edit_text}):
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
                                    if self.updateExec([True, "저장 완료", "저장 실패"], updateProfile, self.select_key, self.login_user_name, update_items):
                                        for items in update_items:
                                            original_data[items[0]] = items[1]
                                        conn.commit()
                                else:
                                    QMessageBox.about(self, "알림", "변경된 데이터가 없습니다.")
                            else:  # profile all
                                if len(update_items):
                                    profile_result = self.updateExec([False], updateProfile, self.select_key, self.login_user_name, update_items)
                                    if profile_result:
                                        for items in update_items:
                                            original_data[items[0]] = items[1]
                                else:
                                    profile_result = 0

                                hobbynspec_input_text = self.lineEdit_profile_hobbynspec.text()
                                if hobbynspec_input_text:
                                    hobbynspec_result = self.updateExec([False], updateHobbynspec, "INSERT",
                                                                        {"key": self.select_key,
                                                                         "user_name": self.login_user_name,
                                                                         "value": hobbynspec_input_text})
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
                    if self.updateExec([True, "삭제 완료", "삭제 실패"], updateHobbynspec, "DELETE",
                                       {"key": self.select_key, "user_name": self.login_user_name, "no": str(v_del_row+1)}):
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
                                               "careers": careers_text,
                                               "user_name": self.login_user_name}
                                data_list = [career_data]
                                if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateCareer, v_mod_type, data_list):
                                    conn.commit()
                                    self.tableDataCreater("career")
                                self.lineEdit_career_careers.setText("")
                    else:
                        QMessageBox.about(self, "알림", "경력에 추가할 값을 입력하세요.")
                elif v_mod_type == "ALL_DELETE":
                    if self.select_info_career:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateCareer, v_mod_type, [{"key": self.select_key}]):
                                conn.commit()
                                self.tableDataCreater("career")
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
                                    if v_mod_type == "UPDATE":
                                        career_data["user_name"] = self.login_user_name
                                    data_list.append(career_data)

                            if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateCareer, v_mod_type, data_list):
                                conn.commit()
                                self.tableDataCreater("career")
                    else:
                        QMessageBox.about(self, "알림", "선택된 데이터가 없습니다.")
            else:
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])

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
            elif table_obj_name in ["tableWidget_contact", "tableWidget_other"]:
                info_data = getattr(self, "select_info_" + table_obj_name[table_obj_name.index("_")+1:])
                for idx, data in enumerate(info_data[item.row()]):
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

                            contact_data["user_name"] = self.login_user_name
                            data_list = [contact_data]
                            if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateContact, v_mod_type, data_list):
                                conn.commit()
                                self.tableDataCreater("contact")
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
                                self.tableDataCreater("contact")
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
                                    contact_data["user_name"] = self.login_user_name
                                    data_list.append(contact_data)
                                else:
                                    for idx, col in enumerate(self.contact_table_cols):
                                        if col == "no":
                                            contact_data["no"] = self.select_info_contact[chk_idx][idx]
                                    data_list.append(contact_data)
                            if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateContact, v_mod_type, data_list):
                                conn.commit()
                                self.tableDataCreater("contact")
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
                    self.tableWidget_contract.setCellWidget(m_idx, 0, tableCheckBox())
                    for r_idx, r_data in enumerate(m_row):
                        if r_idx <= self.contract_data_rng_idx:
                            cell_item = QTableWidgetItem()
                            cell_item.setText(str(r_data) if r_data else "")
                        self.tableWidget_contract.setItem(m_idx, r_idx+1, cell_item)
                # table merge
                for m_idx, m_row in enumerate(self.select_info_contract):
                    for r_idx, r_data in enumerate(m_row):
                        if m_row[r_no_idx] == 1 and r_idx+1 in self.table_merge["contract"]["col"]:
                            self.tableWidget_contract.setSpan(m_idx, r_idx+1, m_row[merge_col_idx], 1)

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
                        self.contract_insert_stmt(v_mod_type)
                elif v_mod_type == "ALL_DELETE":
                    if self.select_info_contract:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateContract, v_mod_type, [{"key": self.select_key}]):
                                conn.commit()
                                self.contractTable()
                    else:
                        QMessageBox.about(self, "알림", "삭제할 데이터가 없습니다.")
                elif v_mod_type == "DISPLAY":  # DISPLAY: 계약정보에 선택 데이터 input
                    checked_list = getCheckListFromTable(self.tableWidget_contract, QCheckBox)
                    if len(checked_list) > 1:
                        QMessageBox.about(self, "알림", "하나의 데이터만 선택하세요.")
                    else:
                        if self.btnExecOrCancel("update") == QMessageBox.Yes:
                            QMessageBox.about(self, "알림", "계약 정보 상단에 선택한 값이 반영되었습니다.\n값을 수정 후 저장 버튼을 클릭하세요.")
                            self.contract_table_selected_index = checked_list[0]
                            self.btn_contract_insert.setText("저장")
                            selected_data = self.select_info_contract[checked_list[0]]
                            contract_data = {"key": self.select_key}
                            contract_data_ap = {"key": self.select_key}
                            for col_idx, col in enumerate(self.contract_table_cols):
                                if col_idx in self.combobox_idx_in_data["contract"]:
                                    getattr(self, "comboBox_contract_" + col).setCurrentText(selected_data[col_idx])
                                    contract_data[col] = selected_data[col_idx] if selected_data[col_idx] is not None else ''
                                else:
                                    try:
                                        if col == "amount" and "~" in selected_data[col_idx]:
                                            amount1_index = self.contract_table_cols.index("amount1")
                                            getattr(self, "lineEdit_contract_" + col).setText(selected_data[amount1_index])
                                        else:
                                            getattr(self, "lineEdit_contract_"+col).setText(selected_data[col_idx])

                                        if col == "ap":
                                            contract_data_ap[col] = selected_data[col_idx] if selected_data[col_idx] is not None else ''
                                        else:
                                            contract_data[col] = selected_data[col_idx] if selected_data[col_idx] is not None else ''
                                    except AttributeError:
                                        continue
                            self.contract_update_org_data = [contract_data, contract_data_ap]  # 테이블 수정 시 원값 저장 변수
                            self.lineEditDisable("contract", True)
                            self.btn_contract_insert.clicked.disconnect()
                            self.btn_contract_insert.clicked.connect(lambda: self.contractDataExec("UPDATE"))
                elif v_mod_type == "UPDATE":
                    if self.contract_insert_stmt(v_mod_type):
                        self.lineEditDisable("contract", False)
                        self.btn_contract_insert.clicked.disconnect()
                        self.btn_contract_insert.clicked.connect(lambda: self.contractDataExec("INSERT"))
                        self.btn_contract_insert.setText("추가")
                else:  # DELETE
                    checked_list = getCheckListFromTable(self.tableWidget_contract, QCheckBox)
                    if checked_list:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            for chk_idx in checked_list:
                                contract_data = {"key": self.select_key}
                                if v_mod_type == "DELETE":
                                    for idx, col in enumerate(self.contract_table_cols):
                                        if col in ["type", "c_month"]:
                                            contract_data[col] = self.select_info_contract[chk_idx][idx]
                                    data_list.append(contract_data)

                            if self.updateExec([True, "삭제 완료", "삭제 실패"], updateContract, v_mod_type, data_list):
                                conn.commit()
                                self.contractTable()
                    else:
                        QMessageBox.about(self, "알림", "선택된 데이터가 없습니다.")
            else:
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])

    def contract_insert_stmt(self, v_mod_type):
        # contract insert / update
        if self.column_value_type_check("contract"):
            contract_data = {"key": self.select_key, "user_name": self.login_user_name}
            contract_data_ap = {"key": self.select_key, "user_name": self.login_user_name}

            for col_idx, col in enumerate(self.contract_table_cols):
                if col_idx in self.combobox_idx_in_data["contract"]:
                    contract_data[col] = getattr(self, "comboBox_contract_" + col).currentText()
                elif col == "type":
                    type_val = nvl(self.lineEdit_contract_type.text(), self.lineEdit_contract_type.placeholderText())
                    contract_data[col] = type_val
                    contract_data_ap[col] = type_val
                elif col == "ap":
                    input_text = self.lineEdit_contract_ap.text()
                    contract_data_ap[col] = input_text
                else:
                    try:
                        input_text = getattr(self, "lineEdit_contract_" + col).text()
                        contract_data[col] = input_text
                    except AttributeError:
                        continue

            data_list = [contract_data, contract_data_ap]
            value_changed = 0 if self.contract_update_org_data[0] == data_list[0] else 1

            # ap값 비교 체크
            ap_change_check = False
            if v_mod_type == "UPDATE" and self.contract_update_org_data[1]["ap"] != data_list[1]["ap"]:
                ap_change_check = True
            elif v_mod_type == "INSERT":
                original_ap_val = ""
                for data in self.select_info_contract:
                    if data[self.contract_table_cols.index("type")] == data_list[0]["type"]:
                        original_ap_val = data[self.contract_table_cols.index("ap")]
                        original_ap_val = original_ap_val if original_ap_val is not None else ""
                        break
                if not original_ap_val:
                    ap_change_check = "pass"
                if original_ap_val != data_list[1]["ap"]:
                    ap_change_check = True

            if ap_change_check:
                if ap_change_check == "pass" or self.btnExecOrCancel("AP값이 저장된 값과 다릅니다. AP값을 변경하시겠습니까?") == QMessageBox.Yes:
                    value_changed += 1
                else:
                    data_list[1]["ap"] = None
            else:
                data_list[1]["ap"] = None

            if value_changed == 0:
                QMessageBox.about(self, "알림", "변경된 내용이 없습니다.")
                return False

            if v_mod_type == "UPDATE":  # 값 검증
                delete_key_list = []
                for key in data_list[0].keys():
                    if key != "key" and key not in self.lineEdit_disable_col["contract"]:
                        if data_list[0][key] == self.contract_update_org_data[0][key]:
                            delete_key_list.append(key)
                for key in delete_key_list:
                    del data_list[0][key]

            ex_msg = [True, "추가 완료.", "데이터 추가 오류 발생"] if v_mod_type == "INSERT" else [True, "수정 완료.", "데이터 수정 오류 발생"]
            if self.updateExec(ex_msg, updateContract, v_mod_type, data_list):
                conn.commit()
                self.contractTable()
            for col_idx, col in enumerate(self.contract_table_cols):
                if col_idx in self.combobox_idx_in_data["contract"]:
                    self.comboBox_contract_c_month.setCurrentIndex(0)
                else:
                    try:
                        getattr(self, "lineEdit_contract_" + col).setText("")
                    except AttributeError:
                        continue
            return True
        
    def otherDataExec(self, v_mod_type):
        data_list = []
        try:
            if self.flag_status:
                if v_mod_type == "INSERT":
                    if self.btnExecOrCancel("save") == QMessageBox.Yes:
                        if self.column_value_type_check("other"):
                            other_data = {"key": self.select_key}
                            for col_idx, col in enumerate(self.other_table_cols):
                                if col in self.table_no_edit_column["other"]:
                                    pass
                                else:
                                    other_data[col] = getattr(self, "lineEdit_other_"+col).text()

                            data_list = [other_data]
                            if self.updateExec([True, "추가 완료.", "데이터 추가 오류 발생"], updateOther, v_mod_type, data_list):
                                conn.commit()
                                self.tableDataCreater("other")
                            for col_idx, col in enumerate(self.other_table_cols):
                                if col in self.table_no_edit_column["other"]:
                                    pass
                                else:
                                    getattr(self, "lineEdit_other_"+col).setText("")
                elif v_mod_type == "ALL_DELETE":
                    if self.select_info_other:
                        if self.btnExecOrCancel("del") == QMessageBox.Yes:
                            if self.updateExec([True, "전체 삭제 완료", "삭제 실패"], updateOther, v_mod_type, [{"key": self.select_key}]):
                                conn.commit()
                                self.tableDataCreater("other")
                    else:
                        QMessageBox.about(self, "알림", "삭제할 데이터가 없습니다.")
                else:  # UPDATE/DELETE
                    checked_list = getCheckListFromTable(self.tableWidget_other, QCheckBox)
                    if checked_list:
                        if self.btnExecOrCancel("save" if v_mod_type == "UPDATE" else "del") == QMessageBox.Yes:
                            for chk_idx in checked_list:
                                other_data = {"key": self.select_key}
                                if v_mod_type == "UPDATE":
                                    original_data = self.select_info_other[chk_idx]
                                    changed_data = []
                                    for col_idx in list(range(self.tableWidget_other.columnCount()))[1:]:
                                        table_item_data = self.tableWidget_other.model().index(chk_idx, col_idx).data()
                                        changed_data.append(table_item_data if table_item_data else None)

                                    for idx, col in enumerate(self.other_table_cols):
                                        if original_data[idx] != changed_data[idx]:
                                            other_data[self.other_table_cols[idx]] = changed_data[idx]
                                    data_list.append(other_data)
                                else:
                                    for idx, col in enumerate(self.other_table_cols):
                                        if col == "no":
                                            other_data["no"] = self.select_info_other[chk_idx][idx]
                                    data_list.append(other_data)
                            if self.updateExec([True, "저장 완료", "저장 실패"] if v_mod_type == "UPDATE" else [True, "삭제 완료", "삭제 실패"], updateOther, v_mod_type, data_list):
                                conn.commit()
                                self.tableDataCreater("other")
                    else:
                        QMessageBox.about(self, "알림", "선택된 데이터가 없습니다.")
            else:
                QMessageBox.about(self, "알림", flag_massage)
        except Exception as e:
            QMessageBox.critical(self, "오류", e.args[0])
        
    def tableDataCreater(self, v_type):
        info_data = globals()["info_"+v_type](self.select_key)
        if info_data:
            setattr(self, v_type + "_table_cols", info_data[0])
            setattr(self, "select_info_" + v_type, info_data[1])

        select_info = getattr(self, "select_info_" + v_type)
        table_obj = getattr(self, "tableWidget_" + v_type)
        if select_info:
            try:
                table_obj.blockSignals(True)
                table_obj.setRowCount(0)

                if v_type == "career":
                    career_data_mod = []
                    for key_type in select_info.keys():
                        career_type_data = select_info[key_type]
                        for key_detail in career_type_data.keys():
                            career_detail_data = career_type_data[key_detail]
                            for key_no in career_detail_data.keys():
                                career_data_mod.append([key_type, key_detail, key_no, career_detail_data[key_no]])

                    select_info = career_data_mod

                for m_idx, m_row in enumerate(select_info):
                    table_obj.insertRow(m_idx)
                    table_obj.setCellWidget(m_idx, 0, tableCheckBox())

                    for r_idx, r_data in enumerate(m_row):
                        if v_type == "contact" and r_idx in self.combobox_idx_in_data[v_type]:
                            inComboBox = QComboBox()
                            inComboBox.addItems(self.comboBox_contact_gubun_list)
                            inComboBox.setCurrentText(r_data)
                            self.tableWidget_contact.setCellWidget(m_idx, r_idx+1, inComboBox)
                        else:
                            cell_item = QTableWidgetItem()
                            cell_item.setText(str(r_data) if r_data else "")
                            table_obj.setItem(m_idx, r_idx + 1, cell_item)

                table_obj.blockSignals(False)
                table_obj.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                table_obj.blockSignals(False)
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()
        else:
            try:
                table_obj.blockSignals(True)
                table_obj.setRowCount(0)
                table_obj.insertRow(0)
                table_obj.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
                table_obj.setSpan(0, 0, 1, table_obj.columnCount())
                table_obj.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)
                table_obj.blockSignals(False)
                table_obj.verticalHeader().setMinimumSectionSize(22)
            except Exception as e:
                table_obj.blockSignals(False)
                QMessageBox.critical(self, "오류", e.args[0])
                self.close()

    def btnExecOrCancel(self, v_exec_type_or_msg):
        question_msg_text = {"save": "저장", "del": "삭제", "update": "수정"}
        if v_exec_type_or_msg in question_msg_text:
            reply = QMessageBox.question(self, " ", question_msg_text[v_exec_type_or_msg] + "하시겠습니까?",
                                         QMessageBox.Yes | QMessageBox.No)
        else:
            reply = QMessageBox.question(self, " ", v_exec_type_or_msg, QMessageBox.Yes | QMessageBox.No)
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

                if data[3] is not None:  # check_string
                    if data[3] in lineEdit_input_text:
                        pass
                    else:
                        message_list.append([obj_lineEdit, label_text.replace(" ", "") + "에 입력된 값에 " + data[3] +
                                             " 문자가 꼭 포함되어야 합니다."])
                        continue

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
    

    def lineEditDisable(self, v_type, v_disabled):
        for col in self.lineEdit_disable_col[v_type]:
            if self.contract_table_cols.index(col) in self.combobox_idx_in_data["contract"]:
                getattr(self, "comboBox_contract_" + col).setDisabled(v_disabled)
            else:
                getattr(self, "lineEdit_" + v_type + "_" + col).setDisabled(v_disabled)

    def buttonRefresh(self, v_type):
        img_file = ":/icon/init.png"
        info_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(img_file).scaled(15, 17, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        info_icon.addPixmap(pixmap, QtGui.QIcon.Active, QtGui.QIcon.Off)
        buttn_init_obj = getattr(self, "btn_"+v_type+"_init")
        buttn_init_obj.setIcon(info_icon)
        buttn_init_obj.clicked.connect(lambda: self.typeLineEditInit(v_type))

    def typeLineEditInit(self, v_type):
        for lineEdit in self.findChildren(QLineEdit):
            if lineEdit.objectName() and v_type in lineEdit.objectName():
                lineEdit.setText("")

        for comboBox in self.findChildren(QComboBox):
            if comboBox.objectName() and v_type in comboBox.objectName():
                comboBox.setCurrentIndex(0)

        if v_type == "contract":
            self.contract_update_org_data = [{}, {}]
            if self.btn_contract_insert.text() != "추가":
                self.lineEditDisable("contract", False)
                self.btn_contract_insert.clicked.disconnect()
                self.btn_contract_insert.clicked.connect(lambda: self.contractDataExec("INSERT"))
                self.btn_contract_insert.setText("추가")

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


def tableCheckBox():
    cellWidget = QWidget()
    layoutCB = QHBoxLayout(cellWidget)
    checkBox = QCheckBox()
    layoutCB.addWidget(checkBox)
    layoutCB.setAlignment(QtCore.Qt.AlignCenter)
    layoutCB.setContentsMargins(0, 0, 0, 0)
    cellWidget.setLayout(layoutCB)

    return cellWidget


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModelWindow("admin", 614)
    app.exec_()