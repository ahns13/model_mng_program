def comboStyleCss(obj_comboBox, v_list_width):
    # 검색 콤보박스 드랍다운 박스 스타일
    obj_comboBox.setStyleSheet("""
        QComboBox QAbstractItemView { min-width: """ + v_list_width + """px; }
        QComboBox QAbstractItemView::item { min-height: 12px; }
        QListView::item:selected { font: 10px; color: blue; background-color: #ebe6df; min-width: 1000px; }"
        """)


def getCheckListFromTable(obj_table, obj_check_box):
    check_idx_list = []
    for r_idx in range(obj_table.rowCount()):
        if obj_table.cellWidget(r_idx, 0).findChild(obj_check_box).checkState():
            check_idx_list.append(r_idx)
    return check_idx_list


def nvl(v_value1, v_value2):
    return v_value1 if v_value1 else v_value2

