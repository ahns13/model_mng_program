import sys
import copy
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *

from model_sql_ui import conn, flagStatus, info_profile, updateProfile, updateHobbynspec


class ModelWindow(QtWidgets.QDialog):
    def __init__(self, v_model_key):
        super(ModelWindow, self).__init__()
        uic.loadUi("./model_info_window.ui", self)  # ui파알을 위젯에 할당할 때 loadUi
        self.select_key = v_model_key

        profile_data = info_profile(v_model_key)
        self.flag_status = flagStatus(self.select_key, 1)  # status[1: 점유, 0: 해제]

        if not self.flag_status:
            QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중입니다.\n변경 내용이 있을 수 있으니 해당 사용자 작업 종료 후 다시 창을 여십시오.\n조회만 가능합니다.")
        # [data_original, data_change]
        self.select_info_profile = [profile_data[0], copy.deepcopy(profile_data[0])]
        self.select_info_profile_hobbynspec = profile_data[1]

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

        self.show()

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
        original_data.append([len(original_data), v_insert_text])
        self.lineEdit_profile_hobbynspec.setText("")

    def closeEvent(self, event):
        flagStatus(self.select_key, 0)


list_btn_style = """
    font-size: 10px;
    font-weight: bold;
    color: #6e6e6e;
    margin: 1px;
    border-radius: 3px;
    border: 1px solid #6e6e6e;
"""

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModelWindow(278)
    app.exec_()
