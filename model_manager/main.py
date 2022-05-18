import sys, math, os
from PyQt5 import QtWidgets
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import *
import copy
import win32com.client

from model_sql_ui import *

form_class = uic.loadUiType("./model_manage_main.ui")[0]


class AlignDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


class IconDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(IconDelegate, self).initStyleOption(option, index)
        option.decorationSize = option.rect.size()


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # tableWidget
        self.tableColCount = 8  # resultl data - total_cnt index
        self.tableColIndexRng = [0, 6]
        self.tableClickIndex = {
            "tablePptFileColIndex": 6,
            "tableDetailInfoIndex": 0
        }

        self.tableWidget.setColumnWidth(0, 60)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.setColumnWidth(2, 85)
        self.tableWidget.setColumnWidth(3, 120)
        self.tableWidget.setColumnWidth(4, 150)
        self.tableWidget.setColumnWidth(5, 80)
        self.tableWidget.setColumnWidth(6, 140)
        self.tableWidget.setColumnWidth(7, 180)
        self.tableWidget.clicked.connect(self.tableClickOpenFile)

        cell_del = AlignDelegate(self.tableWidget)
        self.tableWidget.setItemDelegateForColumn(2, cell_del)

        icon_del = IconDelegate(self.tableWidget)
        self.tableWidget.setItemDelegateForColumn(0, icon_del)

        self.ppt_application = win32com.client.Dispatch("PowerPoint.Application")

        self.noSearchMsg()
        # 버튼: 조회
        self.btn_search.clicked.connect(self.getDefaultTableData)
        self.buttonStyleCss(self.btn_search, "rgb(58, 134, 255)")
        self.btn_next.clicked.connect(lambda: self.tablePaging("next"))
        self.btn_prev.clicked.connect(lambda: self.tablePaging("prev"))

        self.search_types = ("profile", "career", "contact", "contract", "other")

        # modelData
        self.tablePageNo = 0
        self.tableData = []
        self.modelDataLen = 0
        self.maxPageSize = None
        self.pageSize = 20

        # comboBox
        self.combo_data_profile = get_comboBox_list_a("PROFILE")
        self.combo_data_career = get_comboBox_list_career()
        self.combo_data_contact = get_comboBox_list_a("CONTACT")
        self.combo_data_contract = get_comboBox_list_a("CONTRACT")
        self.combo_data_other = get_comboBox_list_a("OTHER")
        self.combo_search_data = {}
        self.search_input_count = {
            "profile": 0,
            "career": 0,
            "contact": 0,
            "contract": 0,
            "other": 0
        }

        list_view = QListView()
        self.combo_profile.setView(list_view)
        list_view = QListView()
        self.combo_career.setView(list_view)
        list_view = QListView()
        self.combo_contact.setView(list_view)
        list_view = QListView()
        self.combo_contract.setView(list_view)

        self.combo_profile.addItems(self.combo_data_profile[0])
        self.combo_career.addItems(self.combo_data_career[0])
        self.combo_contact.addItems(self.combo_data_contact[0])
        self.combo_contract.addItems(self.combo_data_contract[0])

        self.comboStyleCss(self.combo_profile, "90")
        self.comboStyleCss(self.combo_career, "120")
        self.comboStyleCss(self.combo_contact, "120")
        self.comboStyleCss(self.combo_contract, "90")

        for s_type in self.search_types:
            btn_obj = getattr(self, "btn_" + s_type)
            btn_obj.clicked.connect(lambda checked, p_type=s_type: self.searchItemAdd(p_type))
            # lambda 사용 시 for 동적 할당에서 파라미터가 마지막 값으로 할당되기 때문에 lambda 파라미터를 콜백 파라미터 개수에 맞게 설정해줘야 한다.
            # lineEdit returnPressed lambda : 파라미터 2개 생성

        # lineEdit enter 눌렀을 때 처리
        for s_type in self.search_types:
            lineEdit_obj = getattr(self, "lineEdit_" + s_type)
            lineEdit_obj.returnPressed.connect(lambda p_type=s_type: self.searchItemAdd(p_type))
            # lineEdit returnPressed lambda : 파라미터 1개 생성

        self.itemLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.gbox_input_item.setLayout(self.itemLayout)

        # 버튼: 초기화
        self.buttonStyleCss(self.btn_items_clear, "rgb(251, 86, 7)")
        self.btn_items_clear.clicked.connect(lambda: self.deleteItemBtn(True, ""))

        self.show()

    def comboStyleCss(self, obj_comboBox, v_list_width):
        # 검색 콤보박스 드랍다운 박스 스타일
        obj_comboBox.setStyleSheet("""
            QComboBox QAbstractItemView { min-width: """+v_list_width+"""px; }
            QComboBox QAbstractItemView::item { min-height: 12px; }
            QListView::item:selected { font: bold large; color: blue; background-color: #ebe6df; min-width: 1000px; }"
            """)

    def buttonStyleCss(self, obj_button, v_rgb_color):
        # 검색 콤보박스 드랍다운 박스 스타일
        obj_button.setStyleSheet("""
            font-weight: bold;
            color: """ + v_rgb_color + """;
            background-color: white;
            border: 2px solid """ + v_rgb_color + """;
            border-radius: 5px;
            """)

    def searchItemAdd(self, v_search_type):
        # 검색 조건에서 추가  클릭 시 처리
        try:
            cur_combo = getattr(self, "combo_" + v_search_type)
            cur_lineEdit = getattr(self, "lineEdit_" + v_search_type)
            cur_combo_data = getattr(self, "combo_data_" + v_search_type)
            select_combo = cur_combo.currentText()
            input_text = cur_lineEdit.text()
        except AttributeError:  # cur_combo 없으면 기타(other) 처리
            cur_lineEdit = getattr(self, "lineEdit_" + v_search_type)
            cur_combo_data = getattr(self, "combo_data_" + v_search_type)
            select_combo = list(self.combo_data_other[1].keys())[0]
            input_text = cur_lineEdit.text()

        # data_type check
        if v_search_type != "career" and cur_combo_data[1][select_combo][3] == "NUMBER":
            if not input_text.isnumeric():
                QMessageBox.about(self, "알림", "숫자만 입력하세요.")
                cur_lineEdit.clear()
                return

        if input_text:
            input_item = QPushButton(select_combo+":"+input_text)
            input_item.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 버튼 사이즈 텍스트에 맞춤
            input_item.setStyleSheet("font-size: 9pt;")
            input_item.clicked.connect(lambda: self.deleteItemBtn(False, input_item, v_search_type))
            self.itemLayout.addWidget(input_item)
            self.itemLayout.setAlignment(QtCore.Qt.AlignLeft)

            if v_search_type == "career":
                cur_combo_data[1][select_combo].append(input_text)
            else:
                cur_combo_data[1][select_combo][2]["s"].append(input_text)
            self.search_input_count[v_search_type] += 1
            cur_lineEdit.clear()

    def deleteItemBtn(self, v_clear_gbn, clicked_button, v_del_search_type=None):
        # 추가된 검색 항목(버튼)을 클릭하거나 초기화를 눌렀을 때 삭제 처리
        if v_clear_gbn:
            for i in reversed(range(self.itemLayout.count())):
                self.itemLayout.itemAt(i).widget().deleteLater()
            for i_type in self.search_input_count.keys():
                if self.search_input_count[i_type] > 0:
                    cur_combo_data = getattr(self, "combo_data_" + i_type)
                    if i_type == "career":
                        career_search_types = cur_combo_data[1]
                        for c_type in career_search_types.keys():
                            cur_combo_data[1][c_type] = []
                    else:
                        search_types = cur_combo_data[1]
                        for s_type in search_types.keys():
                            cur_combo_data[1][s_type][2]["s"] = []
                    self.search_input_count[i_type] = 0
        else:
            self.itemLayout.removeWidget(clicked_button)
            clicked_button.deleteLater()

            del_btn_info = clicked_button.text().split(":")
            cur_combo_data = getattr(self, "combo_data_" + v_del_search_type)
            if v_del_search_type == "career":
                cur_combo_data[1][del_btn_info[0]].remove(del_btn_info[1])
            else:
                cur_combo_data[1][del_btn_info[0]][2]["s"].remove(del_btn_info[1])
            self.search_input_count[v_del_search_type] -= 1
        self.noSearchMsg()

    def searchDataMaker(self):  # 조회 sql에 전달할 검색 데이터
        profile_data = copy.deepcopy(self.combo_data_profile[1])
        self.combo_search_data = {
            "HOBBYNSPEC": {"취미/특기": profile_data.pop("취미/특기")},
            "PROFILE": profile_data,
            "CAREER": copy.deepcopy(self.combo_data_career[1]),
            "CONTACT": copy.deepcopy(self.combo_data_contact[1]),
            "CONTRACT": copy.deepcopy(self.combo_data_contract[1]),
            "OTHER": copy.deepcopy(self.combo_data_other[1])
        }

    def tableInfoIcon(self):  # 상세정보 icon
        icon_file = "desc_info.ico"
        info_item = QtWidgets.QTableWidgetItem()
        info_icon = QtGui.QIcon()
        info_icon.addPixmap(QtGui.QPixmap(icon_file).scaled(15, 17, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation), QtGui.QIcon.Active, QtGui.QIcon.Off)
        info_item.setIcon(info_icon)
        return info_item

    def tableDataInit(self):  # 테이블 정보 초기화
        self.tablePageNo = 0
        self.tableData = []
        self.modelDataLen = 0
        self.maxPageSize = None
        self.combo_page.clear()

    def getDefaultTableData(self):  # 조회
        self.tableWidget.removeRow(0)
        self.tablePageNo = 1
        self.searchDataMaker()
        self.tableData = get_model_list(self.tablePageNo, self.pageSize, self.combo_search_data)
        self.modelDataLen = self.tableData[0][self.tableColCount]
        self.maxPageSize = math.ceil(self.modelDataLen/self.pageSize)
        self.combo_page.clear()
        self.combo_page.addItems([str(x) for x in range(1, self.maxPageSize+1)])
        self.combo_page.activated.connect(lambda: self.tablePaging(None, self.combo_page.currentText()))

        if self.modelDataLen:
            self.modelDataUpdate(self.tableData)
        else:
            self.noSearchMsg()

    def tablePaging(self, v_btn_type, v_page_no=0):  # 페이지 버튼 및 번호 클릭
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
        self.tableData = get_model_list(self.tablePageNo, self.pageSize, self.combo_search_data)
        self.modelDataUpdate(self.tableData)

    def modelDataUpdate(self, v_model_data):  # sql 결과를 테이블에 업데이트
        self.tableWidget.setRowCount(0)
        for m_idx, m_row in enumerate(v_model_data):
            self.tableWidget.insertRow(m_idx)
            self.tableWidget.setRowHeight(m_idx, 20)
            self.tableWidget.setItem(m_idx, 0, self.tableInfoIcon())
            for r_idx, r_data in enumerate(m_row):
                if self.tableColIndexRng[0] <= r_idx <= self.tableColIndexRng[1]:
                    self.tableWidget.setItem(m_idx, r_idx+1, QTableWidgetItem(str(r_data if r_data else "")))

    def noSearchMsg(self):  # 조회된 결과가 없을 때
        self.tableDataInit()
        self.tableWidget.setRowCount(1)
        self.tableWidget.setSpan(0, 0, 1, self.tableColCount)
        self.tableWidget.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
        self.tableWidget.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)

    def tableClickOpenFile(self, item):
        if item.column() == self.tableClickIndex["tablePptFileColIndex"]:
            if os.path.exists("Z:\\"):  # Z드라이브로 RaiDrive를 설정해야 함
                try:
                    file_path = self.tableData[item.row()][7]
                    self.ppt_application.Presentations.Open(file_path)
                except:
                    QMessageBox.about(self, "알림", "파일이 존재하는지 확인하십시오.")
            else:
                QMessageBox.about(self, "알림", "Z드라이브에 nas 모델 드라이브를 연결하십시오.")
        elif item.column() == self.tableClickIndex["tableDetailInfoIndex"]:
            self.modelClickOpenWindow(self.tableData[item.row()][9])

    def modelClickOpenWindow(self, v_click_model_key):
        model_window = ModelWindow(v_click_model_key)
        model_window.setStyleSheet(info_style)
        model_window.exec_()

    def closeEvent(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()


class ModelWindow(QtWidgets.QDialog):
    def __init__(self, v_model_key):
        super(ModelWindow, self).__init__()
        uic.loadUi("./model_info_window.ui", self)  # ui파알을 위젯에 할당할 때 loadUi
        self.select_key = v_model_key

        profile_data = info_profile(v_model_key)
        self.flag_status = flagStatus(self.select_key, 1)  # status[1: 점유, 0: 해제]
        print('flag: ', self.flag_status)
        if not self.flag_status:
            QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중입니다. 변경 내용이 있을 수 있으니 해당 사용자 작업 종료 후 다시 창을 여십시오. 조회만 가능합니다.")
        # [data_original, data_change]
        self.select_info_profile = [profile_data[0], copy.deepcopy(profile_data[0])]
        self.select_info_profile_hobbynspec = [profile_data[1], copy.deepcopy(profile_data[1])]
        for edit_key in self.select_info_profile[0].keys():
            cur_lineEdit = getattr(self, "lineEdit_profile_" + edit_key)
            cur_lineEdit.setText(self.select_info_profile[0][edit_key])

            cur_btn = getattr(self, "btn_profile_" + edit_key)
            cur_btn.clicked.connect(lambda checked, p_edit_key=edit_key: self.profileSave(p_edit_key))

        self.list_hobbynspec.addItems([d[1] for d in self.select_info_profile_hobbynspec[0]])
        self.btn_profile_hobbynspec.clicked.connect(lambda: self.profileSave("hobbynspec"))
        self.btn_profile_all_save.clicked.connect(lambda: self.profileSave(""))

        self.show()

    def profileSave(self, v_type):
        try:
            if self.flag_status:
                if v_type == "hobbynspec":
                    edit_text = self.lineEdit_profile_hobbynspec.text()
                    self.updateExec(updateHobbynspec(self.select_key, "INSERT", edit_text), len(edit_text))
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
                            input_value = change_data[edit_key].replace(" ", "")
                            if len(input_value):
                                if change_data[edit_key] != original_data[edit_key]:
                                    update_items.append([edit_key, change_data[edit_key]])

                    self.updateExec(updateProfile(self.select_key, update_items), len(update_items))
            else:
                QMessageBox.about(self, "알림", "다른 사용자가 모델 데이터를 작업 중이니 해당 사용자의 작업 종료 후 다시 창을 여십시오.")
        except Exception as e:
            print(e)

    def updateExec(self, fn_sql, v_len_items):
        if v_len_items:
            QMessageBox.about(self, "알림", "저장 완료") if fn_sql else QMessageBox.about(self, "알림", "저장 실패")
        else:
            QMessageBox.about(self, "알림", "변경된 데이터가 없습니다.")

    def closeEvent(self, event):
        flagStatus(self.select_key, 0)


# --- info window stylesheet --- #
info_style = """ 
    QLineEdit {
        font: 11px;
    }
"""


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
