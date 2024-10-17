from quickchart import QuickChart, QuickChartFunction
import random

qc = QuickChart()


def random_color():
    """Generate a random color in hex format."""
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def get_current_chart(labels, current_counts, chart_type, text):
    """
    Create a chart with current counts for each specified Jamf smart group.

    Args:
        labels: List of smart group names.
        current_counts: List of member counts for each group.
        text: Title of the chart.
        chart_type: Type of chart to generate (default: "bar").

    Returns:
        URL of the generated chart.
    """
    qc.background_color = "rgba(0, 0, 0, 0)"
    # predefined segment colors, these are pretty
    segment_colors = ["#28EB4F", "#ff6384", "#ffcd56", "#4bc0c0", "#9966ff", "#ff9f40"]
    # create a list of colors based on the number of labels
    if len(labels) > len(segment_colors):
        # if there are more labels than predefined colors, randomize additional colors
        additional_colors = [
            random_color() for _ in range(len(labels) - len(segment_colors))
        ]
        segment_colors += additional_colors

    # use only as many colors as there are labels
    segment_colors = segment_colors[: len(labels)]
    qc.background_color = "rgba(0, 0, 0, 0)"
    if chart_type == "pie" or chart_type == "doughnut":
        cutout_percentage = (
            50 if chart_type == "doughnut" else 0
        )  # default for doughnut
        datasets = [
            {
                "data": current_counts,
                "backgroundColor": segment_colors,
                "borderColor": "#fff",
                "borderWidth": 2,
            }
        ]
        options = {
            "title": {"display": True, "text": text},
            "responsive": True,
            "legend": {"position": "right"},
            "cutoutPercentage": cutout_percentage,  # specific for doughnut chart
        }
    elif chart_type == "horizontalBar":
        datasets = [
            {
                "data": current_counts,
                "backgroundColor": segment_colors,
            }
        ]
        options = {
            "scales": {
                "xAxes": [
                    {
                        "gridLines": {
                            "display": True,
                            "drawOnChartArea": False,
                            "tickMarkLength": 8,
                            "zeroLineWidth": 1,
                            "zeroLineColor": "black",
                            "color": "black",
                        }
                    }
                ],
                "yAxes": [
                    {
                        "display": True,
                        "position": "left",
                        "gridLines": {
                            "display": True,
                            "drawOnChartArea": False,
                            "tickMarkLength": 8,
                            "color": "black",
                        },
                    }
                ],
            },
            "legend": {"display": False},
            "plugins": {
                "datalabels": {
                    "anchor": "end",
                    "align": "end",
                    "color": "blue",
                    "font": {
                        "size": 10,
                        "weight": "bold",
                    },
                }
            },
        }
        qc.width = 800
        qc.height = 600
        qc.device_pixel_ratio = 2.0
    else:
        # default to bar
        datasets = [
            {
                "label": "Current",
                "data": current_counts,
                "backgroundColor": QuickChartFunction(
                    "getGradientFillHelper('vertical', ['#00FF00', '#FFA500', '#FF0000'])"
                ),
            }
        ]
        options = {
            "title": {"display": True, "text": text},
            "scales": {"xAxes": [{"stacked": True}], "yAxes": [{"stacked": True}]},
            "plugins": {"roundedBars": True},
        }

    # config based on chart type
    qc.config = {
        "type": chart_type,
        "data": {"labels": labels, "datasets": datasets},
        "options": options,
    }

    chart_url = qc.get_url()

    return chart_url
