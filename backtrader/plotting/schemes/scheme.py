from backtrader.plot.scheme import PlotScheme as _BtPlotScheme


class Scheme(_BtPlotScheme):
    def __init__(self):
        super().__init__()

        self.barup_wick = self.barup
        self.bardown_wick = self.bardown

        self.barup_outline = self.barup
        self.bardown_outline = self.bardown

        self.crosshair_line_color = '#999999'

        self.legend_background_color = '#3C3F41'
        self.legend_text_color = 'lightgrey'

        self.loc = 'lightgray'
        self.background_fill = '#222222'
        self.body_fill = "white"
        self.border_fill = "#3C3F41"
        self.legend_click = "hide"  # or "mute"
        self.axis_line_color = 'darkgrey'
        self.tick_line_color = self.axis_line_color
        self.grid_line_color = '#444444'
        self.axis_text_color = 'lightgrey'
        self.plot_title_text_color = 'darkgrey'
        self.axis_label_text_color = 'darkgrey'

        self.xaxis_pos = "all"  # "all" or "bottom"

        self.table_color_even = '#404040'
        self.table_color_odd = '#333333'
        self.table_header_color = '#7a7a7a'

        self.plot_width = 1800
        self.analyzer_tab_width = 1860
        self.analyzer_tab_num_cols = 2
        self.plot_height_data = 800
        self.plot_height_indicator = 400
        self.plot_height_observer = 400
        self.plot_mode = "tabs"

        self.tooltip_background_color = '#4C4F51'
        self.tooltip_text_label_color = '#848EFF'
        self.tooltip_text_value_color = '#aaaaaa'

        self.tab_active_background_color = '#333333'
        self.tab_active_color = '#4C4F51'

        self.text_color = 'lightgrey'

        self.show_headline = True

        """
        hover tooltips of datas will contain all other datas and all indicators/observers
        if set to False then tooltips of datas will only contain the current data and indicators/observers related to that data
        """
        self.merge_data_hovers = True

        self.number_format = '0,0.000'
        self.number_format_volume = '0.00 a'
