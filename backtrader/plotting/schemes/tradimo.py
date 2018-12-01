from .blackly import Blackly


class Tradimo(Blackly):
    def __init__(self):
        super().__init__()

        dark_text = "#333333"

        self.barup = "#265371"
        self.bardown = "#FC5D45"

        self.barup_wick = self.barup
        self.bardown_wick = self.bardown

        self.barup_outline = self.barup
        self.bardown_outline = self.bardown

        self.crosshair_line_color = '#000000'

        self.legend_background_color = '#f5f5f5'
        self.legend_text_color = dark_text
        self.legend_click = "hide"  # or "mute"

        self.loc = '#265371'
        self.background_fill = 'white'
        self.body_fill = "white"
        self.border_fill = "white"
        self.axis_line_color = '#222222'
        self.grid_line_color = '#eeeeee'
        self.tick_line_color = self.axis_line_color
        self.axis_text_color = dark_text
        self.plot_title_text_color = dark_text
        self.axis_label_text_color = dark_text

        self.table_color_even = "#404040"
        self.table_color_odd = "#333333"
        self.table_header_color = "#7a7a7a"

        self.tooltip_background_color = '#f5f5f5'
        self.tooltip_text_label_color = "#848EFF"
        self.tooltip_text_value_color = "#aaaaaa"

        self.tab_active_background_color = '#dddddd'
        self.tab_active_color = '#111111'

        self.text_color = '#222222'

        self.table_color_even = "#fefefefe"
        self.table_color_odd = "#eeeeee"
        self.table_header_color = "#cccccc"
