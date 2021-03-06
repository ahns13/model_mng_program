import math
import os
import time
import gc
import win32com.client
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtGui import QDropEvent

from model_sql_ui import conn, get_model_list, get_comboBox_list_a, get_comboBox_list_career, saveImagePath
from window_info import QtWidgets, uic, QtCore, QtGui, sys, copy, ModelWindow, tableCheckBox
from login import LoginWindow
from model_functions import *
from program_info import image_root
from pptCreater import modelPptMaker
import model_images_rc

import logging
import traceback

logging.basicConfig(filename='./test.log', level=logging.ERROR)

main_ui_path = "./model_manage_main.ui"  # pyinstaller 작업 시 전체 경로 입력
form_class = uic.loadUiType(main_ui_path)[0]


widget_width = 0


def treeWidgetWidth(v_value):
    global widget_width
    widget_width = widget_width if widget_width > v_value else v_value


class IconDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(IconDelegate, self).initStyleOption(option, index)
        option.decorationSize = option.rect.size()  # icon size adjust


class TableDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(TableDelegate, self).initStyleOption(option, index)
        option.font.setPixelSize(12)

        if index.column() in [3, 4, 6]:  # 테이블 칼럼 정렬 - center
            option.displayAlignment = QtCore.Qt.AlignCenter


class TreeWidget(QWidget):
    def __init__(self, txt='', image_path='', font_size=11, tree_path=None, select_image_list=None):
        super().__init__()

        tree_item_font = QtGui.QFont()
        tree_item_font.setPixelSize(font_size)

        layout = QVBoxLayout()
        image_label = QLabel()
        image_label.setFixedSize(150, 150)

        if image_path:
            image = QtGui.QImage(r"{}".format(image_path))
            select_image_list[tree_path] = image
            image = QtGui.QPixmap.fromImage(image).scaledToWidth(160)
            # image = QtGui.QPixmap(r"{}".format(image_path))
            image_label.setPixmap(image)
        layout.addWidget(image_label)

        text_label = QLabel()
        text_label.setText(txt)
        text_label.setFont(tree_item_font)
        layout.addWidget(text_label, QtCore.Qt.AlignLeft)

        self.setLayout(layout)
        treeWidgetWidth(self.sizeHint().width())


class DropLabel(QLabel):
    def __init__(self, parent, groupBox):
        super(DropLabel, self).__init__(groupBox)
        self.parent = parent
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 1px solid rgb(166, 166, 166)")

    def dragEnterEvent(self, e):
        if type(e.source()) == QTreeWidget:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        drag_item = e.source().selectedItems()[0]
        if drag_item.text(0):
            path = drag_item.text(0)
        else:  # image item
            item_widget = e.source().itemWidget(drag_item, 0)
            path = item_widget.findChildren(QLabel)[1].text()
        while drag_item.parent():
            drag_item = drag_item.parent()
            path = drag_item.text(0)+"/"+path

        try:
            target_size = self.size()
            image = QtGui.QPixmap.fromImage(self.parent.select_model_images[self.parent.select_model_index][path]) \
                .scaled(target_size, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            self.setPixmap(image)
        except Exception as e:
            print(e)


class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.login_user_name = None

        # tableWidget var
        self.dataColCountIndex = 9  # total_cnt index of data
        self.dataToTableMapIndex = [1,3,4,5,6,7,8]  # tableIndex
        self.tableClickIndex = {
            "tablePptFileColIndex": 7,
            "tableDetailInfoIndex": 0
        }
        self.dataKeyIndex = 9
        self.dataNameIndex = 0
        self.fileNameIndex = 5
        self.filePathIndexOfData = 10
        self.imageFolderIndex = [7, 9]  # index pair : data, tableColumn

        # tableWidget
        self.tableWidget.setColumnWidth(0, 60)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.setColumnWidth(2, 70)
        self.tableWidget.setColumnWidth(3, 80)
        self.tableWidget.setColumnWidth(4, 110)
        self.tableWidget.setColumnWidth(5, 130)
        self.tableWidget.setColumnWidth(6, 80)
        self.tableWidget.setColumnWidth(7, 130)
        self.tableWidget.setColumnWidth(8, 170)
        self.tableWidget.setColumnWidth(9, 110)
        self.tableWidget.clicked.connect(self.tableClickOpenFile)
        self.tableWidget.horizontalHeader().setFont(QtGui.QFont("", 8))
        self.tableWidget.verticalHeader().setDefaultSectionSize(15)
        self.tableWidget.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget.setWordWrap(False)

        # tableWidget_select_list
        self.tableWidget_select_list.setColumnWidth(0, 35)
        self.tableWidget_select_list.setColumnWidth(2, 50)
        self.tableWidget_select_list.horizontalHeader().setFont(QtGui.QFont("", 8))
        self.tableWidget_select_list.verticalHeader().setDefaultSectionSize(15)
        self.tableWidget_select_list.verticalHeader().setMinimumSectionSize(22)
        self.tableWidget_select_list.clicked.connect(self.addImagesForClickedModel)

        self.select_model_data = []
        self.select_model_images = {}
        self.select_model_image_locations = {}

        # ------------ #
        icon_delegate = IconDelegate(self.tableWidget)
        self.tableWidget.setItemDelegateForColumn(0, icon_delegate)

        table_delegate = TableDelegate(self.tableWidget)
        self.tableWidget.setItemDelegate(table_delegate)
        self.tableWidget_select_list.setItemDelegate(table_delegate)

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

        comboStyleCss(self.combo_profile, "90")
        comboStyleCss(self.combo_career, "120")
        comboStyleCss(self.combo_contact, "120")
        comboStyleCss(self.combo_contract, "90")

        for s_type in self.search_types:
            btn_obj = getattr(self, "btn_" + s_type)
            btn_obj.clicked.connect(lambda checked, p_type=s_type: self.searchItemAdd(p_type))

        # lineEdit enter 눌렀을 때 처리
        for s_type in self.search_types:
            lineEdit_obj = getattr(self, "lineEdit_" + s_type)
            lineEdit_obj.returnPressed.connect(lambda p_type=s_type: self.searchItemAdd(p_type))

        self.itemLayout = QBoxLayout(QBoxLayout.LeftToRight)
        self.gbox_input_item.setLayout(self.itemLayout)

        # 버튼: 초기화
        self.buttonStyleCss(self.btn_items_clear, "rgb(251, 86, 7)")
        self.btn_items_clear.clicked.connect(lambda: self.deleteItemBtn(True, ""))

        # 버튼: 신규
        self.buttonStyleCss(self.btn_new, "rgb(58, 134, 255)")
        self.btn_new.clicked.connect(lambda: self.modelClickOpenWindow(""))

        # lineEdit range value
        self.comboBoxRangeConnect()

        # treeWidget
        self.treeWidget_images.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)  # treeWidget_images 드래그 설정
        self.treeWidget_images.setDragEnabled(True)
        self.treeWidget_images.setHeaderLabels(["이미지 폴더 목록"])
        self.treeWidget_images.setStyleSheet("""
            QTreeWidget { font-size: 12px; }
            QHeaderView::section {
                background-color: #eee;
            }
            QTreeWidget::Item {
                border: 1px solid #c1c1c1;
                color: #3d3e40;
            }
        """)

        # self.loginCheck()

        # treewidget progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(1250, 440, 150, 25)
        self.progress_rate = 0
        self.directory_size = 0  # 클릭한 모델의 이미지 폴더의 item 수
        self.progress_bar.hide()

        self.textEdit_loading.hide()

        # 컴카드 생성
        self.btn_ppt_maker.clicked.connect(self.modelPptMaker)

        self.label_m1 = DropLabel(self, self.groupBox_ppt1)
        self.label_m1.setGeometry(20, 15, 91, 81)
        self.label_m2 = DropLabel(self, self.groupBox_ppt1)
        self.label_m2.setGeometry(120, 15, 91, 81)
        self.label_s1 = DropLabel(self, self.groupBox_ppt1)
        self.label_s1.setGeometry(20, 105, 41, 61)
        self.label_s2 = DropLabel(self, self.groupBox_ppt1)
        self.label_s2.setGeometry(70, 105, 41, 61)
        self.label_s3 = DropLabel(self, self.groupBox_ppt1)
        self.label_s3.setGeometry(120, 105, 41, 61)
        self.label_s4 = DropLabel(self, self.groupBox_ppt1)
        self.label_s4.setGeometry(170, 105, 41, 61)

        self.btn_ppt_loc_save.clicked.connect()

        self.show()

    def buttonStyleCss(self, obj_button, v_rgb_color):
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
            if "~" in input_text:
                for text in input_text.replace(" ", "").split("~"):
                    if text and not text.isnumeric():
                        QMessageBox.about(self, "알림", "숫자만 입력하세요.")
                        cur_lineEdit.clear()
                        return
            elif not input_text.isnumeric():
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
            elif cur_combo_data[1][select_combo][4] == "Y" and "~" in input_text:
                range_text = input_text.replace(" ", "").split("~")
                cur_combo_data[1][select_combo][2]["ge"] = range_text[0]
                cur_combo_data[1][select_combo][2]["le"] = range_text[1]
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
                            cur_combo_data[1][s_type][2] = {"s": [], "ge": "", "le": ""}
                    self.search_input_count[i_type] = 0
        else:
            self.itemLayout.removeWidget(clicked_button)
            clicked_button.deleteLater()

            del_btn_info = clicked_button.text().split(":")
            cur_combo_data = getattr(self, "combo_data_" + v_del_search_type)
            if v_del_search_type == "career":
                cur_combo_data[1][del_btn_info[0]].remove(del_btn_info[1])
            elif cur_combo_data[1][del_btn_info[0]][4] == "Y" and "~" in del_btn_info[1]:
                cur_combo_data[1][del_btn_info[0]][2]["ge"] = ""
                cur_combo_data[1][del_btn_info[0]][2]["le"] = ""
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
        try:
            img_file = ":/icon/ppt.png"
            info_item = QtWidgets.QTableWidgetItem()
            info_icon = QtGui.QIcon()
            info_icon.addPixmap(QtGui.QPixmap(img_file).scaled(15, 17, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation), QtGui.QIcon.Active, QtGui.QIcon.Off)
            info_item.setIcon(info_icon)
            return info_item
        except Exception as e:
            print(e)
            conn.close()
            sys.exit()

    def tableFolderColumn(self, v_row_index, v_path):  # 이미지경로 button : image + text
        try:
            cellWidget = QWidget()
            layoutCB = QHBoxLayout(cellWidget)
            list_button = QPushButton()
            list_button.setFixedWidth(20)

            img_file = ":/icon/folder.png"
            info_icon = QtGui.QIcon()
            info_icon.addPixmap(
                QtGui.QPixmap(img_file).scaled(17, 19, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation),
                QtGui.QIcon.Active, QtGui.QIcon.Off)
            list_button.setIcon(info_icon)
            list_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            list_button.setToolTip("버튼을 눌러 폴더 목록에서\n모델에 맞는 폴더를 선택해\n이미지 폴더를 연결할 수 있습니다.")
            list_button.clicked.connect(lambda checked, p_row_index=v_row_index: self.openImageFolder(p_row_index))
            layoutCB.addWidget(list_button)

            list_label = QLabel()
            list_label.setText("매핑 완료" if v_path else "X")
            label_font = QtGui.QFont()
            label_font.setPixelSize(12)
            list_label.setFont(label_font)
            list_label.setAlignment(QtCore.Qt.AlignCenter)
            layoutCB.addWidget(list_label)

            layoutCB.setContentsMargins(0, 0, 0, 0)
            cellWidget.setLayout(layoutCB)
            return cellWidget
        except Exception as e:
            conn.close()
            sys.exit()

    def openImageFolder(self, v_row_index):
        msgbox = QMessageBox()
        msgbox.setWindowTitle("이미지 매핑 설정")
        msgbox.setText('매핑을 등록 또는 삭제를 위해\n버튼을 클릭하세요.')

        add_btn = msgbox.addButton('매핑 등록', QtWidgets.QMessageBox.YesRole)
        del_btn = msgbox.addButton('매핑 삭제', QtWidgets.QMessageBox.YesRole)
        msgbox.addButton('취소', QtWidgets.QMessageBox.NoRole)

        msgbox.exec_()
        # reply = msgbox.buttonRole(msgbox.clickedButton())
        # yes: 0, no: 1
        if msgbox.clickedButton() == add_btn:
            self.imageMapAdd(v_row_index)
        elif msgbox.clickedButton() == del_btn:
            self.imageMapDel(v_row_index)

    def imageMapAdd(self, v_row_index):
        click_model = list(map(self.tableData[v_row_index].__getitem__, [self.dataKeyIndex, self.dataNameIndex]))
        image_path = QtWidgets.QFileDialog.getExistingDirectory(None, click_model[1], image_root,
                                                          QtWidgets.QFileDialog.ShowDirsOnly)
        if image_path:
            image_path = os.path.abspath(image_path)
            if image_path == os.path.abspath(image_root):
                QMessageBox.about(self, "알림", "기존 폴더를 대상으로 지정할 수 없습니다. 모델 폴더를 선택해 주세요.")
                self.imageMapAdd(self, v_row_index)
            else:
                if saveImagePath("insert", click_model[0], image_path):
                    conn.commit()
                    self.tableWidget.cellWidget(v_row_index, self.imageFolderIndex[1]).findChild(QLabel).setText("매핑 완료")
                    self.tableData[v_row_index][self.imageFolderIndex[0]] = image_path
                    QMessageBox.about(self, "알림", "매핑 성공")

    def imageMapDel(self, v_row_index):
        click_model = list(map(self.tableData[v_row_index].__getitem__, [self.dataKeyIndex, self.dataNameIndex]))
        if saveImagePath("delete", click_model[0]):
            conn.commit()
            self.tableWidget.cellWidget(v_row_index, self.imageFolderIndex[1]).findChild(QLabel).setText("X")
            self.tableData[v_row_index][self.imageFolderIndex[0]] = ""
            QMessageBox.about(self, "알림", "매핑 삭제 완료")

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
        self.modelDataLen = self.tableData[0][self.dataColCountIndex]
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
            self.tableWidget.setItem(m_idx, 0, self.tableInfoIcon())
            for r_idx, r_data in enumerate(m_row):
                if r_idx < len(self.dataToTableMapIndex):
                    self.tableWidget.setItem(m_idx, self.dataToTableMapIndex[r_idx], QTableWidgetItem(str(r_data if r_data else "")))

            # list add button
            self.tableWidget.setCellWidget(m_idx, 2, self.tableButton(
                "+", self.tableSelectListAdd, model_name=self.tableData[m_idx][self.dataNameIndex], table_index=m_idx))
            # image folder
            self.tableWidget.setCellWidget(m_idx, self.imageFolderIndex[1], self.tableFolderColumn(
                m_idx, m_row[self.imageFolderIndex[0]]))

        self.tableWidget.blockSignals(False)

    def noSearchMsg(self):  # 조회된 결과가 없을 때
        self.tableDataInit()
        self.tableWidget.setRowCount(0)
        self.tableWidget.insertRow(0)
        self.tableWidget.setSpan(0, 0, 1, self.tableWidget.columnCount())
        self.tableWidget.setItem(0, 0, QTableWidgetItem("조회된 데이터가 없습니다."))
        self.tableWidget.item(0, 0).setTextAlignment(QtCore.Qt.AlignCenter)
        self.tableWidget.blockSignals(True)

    def tableClickOpenFile(self, item):
        if item.column() == self.tableClickIndex["tablePptFileColIndex"]:
            reply = QMessageBox.question(self, " ", "선택한 모델의 ppt 파일을 실행합니다.",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if os.path.exists("Z:\\Chicmodle agency\\"):  # Z드라이브로 RaiDrive를 설정해야 함
                    try:
                        file_path = self.tableData[item.row()][self.filePathIndexOfData]
                        self.ppt_application.Presentations.Open(file_path)
                    except:
                        QMessageBox.about(self, "알림", "파일이 존재하는지 확인하십시오.")
                else:
                    QMessageBox.about(self, "알림", "Z드라이브에 nas 모델 드라이브를 연결하십시오.")
        elif item.column() == self.tableClickIndex["tableDetailInfoIndex"]:
            self.modelClickOpenWindow(self.tableData[item.row()][self.dataKeyIndex], self.tableData[item.row()][self.dataNameIndex])

    def comboBoxRangeConnect(self):
        for type in self.search_types:
            try:
                combo_obj = getattr(self, "combo_" + type)
                combo_obj.activated.connect(lambda index, p_type=type, p_combo=combo_obj: self.lineEditRangeSearch(p_type, p_combo))
            except Exception as e:
                continue

    def lineEditRangeSearch(self, v_type, v_combo_obj):
        comboData = getattr(self, "combo_data_" + v_type)
        lineEdit_obj = getattr(self, "lineEdit_" + v_type)
        if comboData[1][v_combo_obj.currentText()][4] == "Y":
            lineEdit_obj.setPlaceholderText("범위 99~999")
            lineEdit_obj.setStyleSheet("QLineEdit { font: 12px }")
        else:
            lineEdit_obj.setPlaceholderText("")

    def tableButton(self, v_btn_text, v_click_function, **kwargs):
        cellWidget = QWidget()
        layoutCB = QHBoxLayout(cellWidget)
        list_button = QPushButton(v_btn_text)
        list_button.setFixedWidth(20)
        list_button.setStyleSheet(list_add_button)
        list_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        list_button.clicked.connect(lambda args=kwargs: v_click_function(kwargs))
        layoutCB.addWidget(list_button)
        layoutCB.setAlignment(QtCore.Qt.AlignCenter)
        layoutCB.setContentsMargins(0, 0, 0, 0)
        cellWidget.setLayout(layoutCB)
        return cellWidget

    def tableSelectListAdd(self, v_args):
        # image table에 선택 모델 추가
        row_index = self.tableWidget_select_list.rowCount()
        self.tableWidget_select_list.insertRow(row_index)
        self.tableWidget_select_list.setCellWidget(row_index, 0, tableCheckBox())
        self.tableWidget_select_list.setItem(row_index, 1, QTableWidgetItem(v_args["model_name"]))
        self.tableWidget_select_list.setCellWidget(row_index, 2, self.tableButton("X", self.selectListRemoveRow, index=row_index))
        self.select_model_data.append(self.tableData[v_args["table_index"]])

    def selectListRemoveRow(self, v_index):
        self.tableWidget_select_list.removeRow(v_index["index"])
        self.select_model_data.pop(v_index["index"])
        self.treeWidget_images.clear()

    def modelClickOpenWindow(self, v_click_model_key, v_click_model_name=None):
        model_window = ModelWindow(self.login_user_name, v_click_model_key)
        model_window.setWindowTitle(model_window.windowTitle() + " - " + (v_click_model_name if v_click_model_name else "신규"))
        model_window.exec_()

    def loginCheck(self):
        login_window = LoginWindow()
        login_window.exec_()

    def folderMaker(self, v_file_path, v_parent_tree, v_tree_depth, v_item_row, v_tree_path):
        v_tree_depth += 1
        folder_list = os.scandir(v_file_path)

        # recursive 함수 적용 시 connect 함수에 파라미터로 timer instance도 넘겨야 한다.
        _timer = QtCore.QTimer()
        _timer.timeout.connect(lambda: self.imageMaker(folder_list, v_parent_tree, v_tree_depth, v_item_row, _timer, v_tree_path))
        _timer.start(10)

    def imageMaker(self, v_folder_list, v_parent_tree, v_tree_depth, v_item_row, v_timer, v_tree_path):
        try:
            self.progress_rate += 1
            self.progress_bar.setValue(math.floor(self.progress_rate/self.directory_size*100))
            time.sleep(0.25)
            f = next(v_folder_list)
        except StopIteration:
            v_timer.stop()
            v_timer.deleteLater()
            timer_cnt = 0
            for obj in gc.get_objects():
                if isinstance(obj, QtCore.QTimer):
                    timer_cnt += 1
            if timer_cnt == 1:
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(False)
                self.textEdit_loading.setVisible(False)
        else:
            if f.is_file() and f.name.split(".")[1].lower() in ["jpg", "jpeg", "png", "gif"]:
                item_f = QTreeWidgetItem(v_parent_tree)
                image_f = TreeWidget(f.name, f.path, tree_path=v_tree_path+"/"+f.name, select_image_list=self.select_model_images[v_item_row])
                self.treeWidget_images.setItemWidget(item_f, 0, image_f)
            elif f.is_dir():
                item_f = QTreeWidgetItem(v_parent_tree)
                item_f.setText(0, f.name)
                self.folderMaker(f.path, item_f, v_tree_depth, v_item_row, v_tree_path+"/"+f.name)
            else:
                item_f = QTreeWidgetItem(v_parent_tree)
                item_f.setText(0, f.name)

    def addImagesForClickedModel(self, item):
        if self.select_model_data[item.row()][self.imageFolderIndex[0]]:
            pass
        else:
            QMessageBox.critical(self, "알림", "이미지 경로가 매핑되지 않았습니다. 모델의 이미지가 존재하는 폴더를 설정하세요.")
            return

        self.select_model_images[item.row()] = {}
        self.select_model_index = item.row()
        self.select_model_image_locations[item.row()] = {"m1": None, "m2": None, "s1": None, "s2": None, "s3": None, "s4": None}

        if item.column() == 1:
            if os.path.exists("Z:\\Chicmodle agency\\"):
                global widget_width
                widget_width = 0
                tree_depth = 1

                self.treeWidget_images.clear()
                self.treeWidget_images.setColumnCount(1)
                item_top = QTreeWidgetItem(self.treeWidget_images, [item.data()])
                try:
                    self.getDirectorySize(self.select_model_data[item.row()][self.imageFolderIndex[0]])
                    if self.directory_size:
                        self.textEdit_loading.setVisible(True)
                        self.progress_bar.setVisible(True)
                        time.sleep(0.3)
                        self.folderMaker(self.select_model_data[item.row()][self.imageFolderIndex[0]], item_top,
                                         tree_depth, item.row(), item.data())
                        self.treeWidget_images.setColumnWidth(0, self.treeWidget_images.indentation() *
                                                              (tree_depth + 1) + widget_width)
                    else:
                        QMessageBox.about(self, "알림", "폴더에 아무것도 존재하지 않습니다.")
                        self.textEdit_loading.setVisible(False)
                        self.progress_bar.setVisible(False)
                except FileNotFoundError:
                    QMessageBox.about(self, "알림", "해당 모델의 파일이 존재하지 않습니다. 확인하세요.")
            else:
                QMessageBox.critical(self, "오류", "모델 DB가 Z드라이브에 연결되어 있는지 학인하세요.")

    def getDirectorySize(self, v_file_path):
        folder_list = os.scandir(v_file_path)
        for f in folder_list:
            self.directory_size += 1
            if f.is_dir():
                self.getDirectorySize(f.path)

    def modelPptMaker(self):
        model_checked_list = getCheckListFromTable(self.tableWidget_select_list, QCheckBox)
        if model_checked_list:
            model_keys, model_names, file_names, file_paths = [], [], [], []
            for idx in model_checked_list:
                selected_model_info = self.select_model_data[idx]
                model_keys.append(selected_model_info[self.dataKeyIndex])
                model_names.append(selected_model_info[self.dataNameIndex])
                file_names.append(selected_model_info[self.fileNameIndex])
                file_paths.append(selected_model_info[self.imageFolderIndex[0]])
            modelPptMaker(name=model_names, file_name=file_names, file_path=file_paths)
        else:
            QMessageBox.about(self, "알림", "컴카드를 만들 모델을 하나 이상 선택하세요.")

    def save_ppt_image_location(self):
        self.select_model_image_locations

    def closeEvent(self, event):
        # 메인 윈도우 종료 시 모든 윈도우 종료
        for window in QApplication.topLevelWidgets():
            window.close()
        conn.close()


list_add_button = """
    font-size: 11px;
    font-weight: bold;
    color:  rgb(255, 0, 110);
    background-color: white;
    border: 1px solid rgb(255, 0, 110);
    border-radius: 5px;
    padding-top: 1px;
"""


if __name__ == "__main__":
    # jpg, jpeg를 인식하지 못할 때 plugins 위치를 추가하면 인식됨
    QtCore.QCoreApplication.addLibraryPath(r"..\model_env\Lib\site-packages\PyQt5\Qt5\plugins")
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    app.exec_()
