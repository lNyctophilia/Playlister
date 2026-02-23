BG_MAIN = "#0a0e27"
BG_PANEL = "#141832"
BG_NAV = "#0d1230"
BG_INPUT = "#1a1e3d"
BG_TREE = "#111530"
BG_STATUS = "#0d1230"
BG_PLAYER = "#0d1230"

BORDER = "#252a4a"

FG_PRIMARY = "#e8eaed"
FG_SECONDARY = "#8b95a5"
FG_LINK = "#74b9ff"

BTN_PRIMARY = "#3b5bdb"
BTN_PRIMARY_HOVER = "#4c6ef5"
BTN_DANGER = "#e03131"
BTN_DANGER_HOVER = "#f03e3e"
BTN_INFO = "#1098ad"
BTN_INFO_HOVER = "#15aabf"
BTN_CONFIRM = "#1c7ed6"
BTN_CONFIRM_HOVER = "#339af0"
BTN_ACCENT = "#7048e8"
BTN_ACCENT_HOVER = "#845ef7"
BTN_SECONDARY = "#253470"
BTN_SECONDARY_HOVER = "#2e3f85"

NAV_ACTIVE = "#4c6ef5"
NAV_INACTIVE = "#1e2247"
NAV_HOVER = "#2a3070"

TREE_ODD = "#111530"
TREE_EVEN = "#161a3a"
TREE_SELECTED = "#364fc7"
TREE_HEADING_BG = "#1a1e3d"
TREE_HEADING_FG = "#8b95a5"

TOOLTIP_BG = "#1a1e3d"
TOOLTIP_FG = "#e8eaed"

MENU_BG = "#141832"
MENU_FG = "#e8eaed"
MENU_ACTIVE_BG = "#3b5bdb"
MENU_ACTIVE_FG = "#ffffff"

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

FONT_NAV = (FONT_FAMILY, 10, "bold")
FONT_HEADING = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 9)
FONT_BUTTON = (FONT_FAMILY, 9, "bold")
FONT_STATUS = (FONT_MONO, 9)
FONT_SMALL = (FONT_FAMILY, 8)
FONT_TOOLTIP = (FONT_FAMILY, 8)


def apply_hover(widget, normal_bg, hover_bg, normal_fg="#e8eaed", hover_fg="#ffffff"):
    def on_enter(e):
        if widget.cget("state") != "disabled":
            widget.config(bg=hover_bg, fg=hover_fg)
    def on_leave(e):
        if widget.cget("state") != "disabled":
            widget.config(bg=normal_bg, fg=normal_fg)
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def style_button(btn, bg=None, fg=FG_PRIMARY, hover_bg=None):
    if bg is None:
        bg = BTN_PRIMARY
    if hover_bg is None:
        hover_bg = BTN_PRIMARY_HOVER
    btn.config(
        bg=bg, fg=fg,
        relief="flat", borderwidth=0,
        font=FONT_BUTTON,
        padx=12, pady=4,
        activebackground=hover_bg,
        activeforeground=fg,
        cursor="hand2"
    )
    apply_hover(btn, bg, hover_bg, fg, fg)


def style_entry(entry):
    entry.config(
        bg=BG_INPUT, fg=FG_PRIMARY,
        insertbackground=FG_PRIMARY,
        relief="flat", borderwidth=1,
        highlightbackground=BORDER,
        highlightcolor=BTN_PRIMARY,
        highlightthickness=1,
        font=FONT_BODY
    )


def style_label(label, fg=None, bg=None, font=None):
    if fg is None:
        fg = FG_PRIMARY
    if bg is None:
        bg = BG_PANEL
    if font is None:
        font = FONT_BODY
    label.config(bg=bg, fg=fg, font=font)


def style_frame(frame, bg=None):
    if bg is None:
        bg = BG_PANEL
    frame.config(bg=bg)


def configure_ttk_styles(style):
    try:
        style.theme_use("clam")
    except:
        pass

    style.configure("Treeview",
        background=BG_TREE,
        fieldbackground=BG_TREE,
        foreground=FG_PRIMARY,
        rowheight=30,
        borderwidth=0,
        font=FONT_BODY
    )

    style.configure("Treeview.Heading",
        font=(FONT_FAMILY, 9, "bold"),
        background=TREE_HEADING_BG,
        foreground=TREE_HEADING_FG,
        relief="flat",
        borderwidth=0
    )

    style.map("Treeview",
        background=[('selected', TREE_SELECTED)],
        foreground=[('selected', '#ffffff')]
    )

    style.map("Treeview.Heading",
        background=[('active', BORDER)],
        foreground=[('active', FG_PRIMARY)]
    )

    style.configure("TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=FG_PRIMARY,
        arrowcolor=FG_SECONDARY,
        borderwidth=1,
        relief="flat"
    )

    style.map("TCombobox",
        fieldbackground=[('readonly', BG_INPUT)],
        foreground=[('readonly', FG_PRIMARY)],
        selectbackground=[('readonly', BG_INPUT)],
        selectforeground=[('readonly', FG_PRIMARY)]
    )

    style.configure("Horizontal.TScale",
        background=BG_PLAYER,
        troughcolor=BORDER,
        sliderrelief="flat"
    )

    style.configure("Vertical.TScrollbar",
        background=BG_PANEL,
        troughcolor=BG_MAIN,
        arrowcolor=FG_SECONDARY,
        borderwidth=0
    )

    style.map("Vertical.TScrollbar",
        background=[('active', BORDER)]
    )

    style.configure("TLabelframe",
        background=BG_PANEL,
        foreground=FG_PRIMARY,
        bordercolor=BORDER
    )

    style.configure("TLabelframe.Label",
        background=BG_PANEL,
        foreground=FG_SECONDARY,
        font=(FONT_FAMILY, 10, "bold")
    )
