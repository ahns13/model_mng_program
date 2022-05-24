def comboStyleCss(obj_comboBox, v_list_width):
    # 검색 콤보박스 드랍다운 박스 스타일
    obj_comboBox.setStyleSheet("""
        QComboBox QAbstractItemView { min-width: """ + v_list_width + """px; }
        QComboBox QAbstractItemView::item { min-height: 12px; }
        QListView::item:selected { font: 10px; color: blue; background-color: #ebe6df; min-width: 1000px; }"
        """)

