# downloads page - paste this into main.py
# Insert after _build_flash_page and _on_detail_loaded

def _build_downloads_page(self):
    self.downloads_page = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(48, 40, 48, 0)
    layout.setSpacing(16)

    top_bar = QHBoxLayout()
    back_btn = SecondaryButton("\u2190  返回")
    back_btn.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.device_list_page))
    top_bar.addWidget(back_btn)
    title = QLabel("已下载设备")
    title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 62px; font-weight: bold; margin-left: 16px;")
    top_bar.addWidget(title, stretch=1)
    layout.addLayout(top_bar)

    self.dl_mgr_scroll = QScrollArea()
    self.dl_mgr_scroll.setStyleSheet(f"""
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: {Theme.BG_DARK};
            width: 48px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: #334155;
            min-height: 40px;
            border-radius: 12px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #475569;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {Theme.BG_DARK};
            height: 48px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: #334155;
            min-width: 40px;
            border-radius: 12px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #475569;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """)
    self.dl_mgr_scroll.setWidgetResizable(True)
    self.dl_mgr_container = QWidget()
    self.dl_mgr_layout = QVBoxLayout()
    self.dl_mgr_layout.setContentsMargins(0, 16, 0, 0)
    self.dl_mgr_layout.setSpacing(12)
    self.dl_mgr_layout.addStretch()
    self.dl_mgr_container.setLayout(self.dl_mgr_layout)
    self.dl_mgr_scroll.setWidget(self.dl_mgr_container)
    layout.addWidget(self.dl_mgr_scroll, stretch=1)
    self.downloads_page.setLayout(layout)
    self.content_stack.addWidget(self.downloads_page)


def _refresh_downloads_list(self):
    layout = self.dl_mgr_layout
    while layout.count() > 1:
        item = layout.takeAt(0)
        if item and item.widget():
            item.widget().deleteLater()
    if not self.downloaded_devices:
        lbl = QLabel("暂无已下载设备\n请从设备列表选择设备下载")
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 42px; padding: 40px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.insertWidget(0, lbl)
        return
    for d in reversed(self.downloaded_devices):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: """ + Theme.BG_CARD + """;
                border-radius: 12px;
                padding: 24px 32px;
            }
        """)
        cl = QVBoxLayout()
        cl.setSpacing(6)
        name = QLabel(d['name'])
        name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 44px; font-weight: bold;")
        cl.addWidget(name)
        info = QLabel(f"设备: {d['codename']} · 版本: {d['version']} · {d['time']}")
        info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 32px;")
        cl.addWidget(info)
        path_lbl = QLabel(f"\U0001f4c1  {d['path']}")
        path_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 32px;")
        cl.addWidget(path_lbl)
        card.setLayout(cl)
        layout.insertWidget(layout.count() - 1, card)