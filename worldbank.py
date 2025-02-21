from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from pandas_datareader import wb
from datetime import datetime

app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])

indicators = {
    "IT.NET.USER.ZS": "Individuals using the Internet (% of population)",
    "SG.GEN.PARL.ZS": "Proportion of seats held by women in national parliaments (%)",
    "EN.GHG.CO2.IP.MT.CE.AR5": "CO2 emissions from Industrial Processes",
}

# get country name and ISO id for mapping on choropleth
countries = wb.get_countries()
#print(countries.to_string())
countries["capitalCity"].replace({"": None}, inplace=True)
#print(countries.to_string())
countries.dropna(subset=["capitalCity"], inplace=True)
countries = countries[["name", "iso3c"]]
#print(countries.to_string())
countries = countries[countries["name"] != "Kosovo"]
countries = countries[countries["name"] != "Korea, Dem. People's Rep."]
#print(countries.to_string())
countries = countries.rename(columns={"name": "country"})
#print(countries.to_string())


def update_wb_data():
    # Retrieve specific world bank data from API
    #print(list(indicators))
    df = wb.download(
        indicator=(list(indicators)), country=countries["iso3c"], start=2005, end=2016
    )
    df = df.reset_index()
    #print(f"DF AFTER RESET INDEX: {df.head().to_string()}")
    df.year = df.year.astype(int)

    # Add country ISO3 id to main df
    df = pd.merge(df, countries, on="country")
    df = df.rename(columns=indicators)
    #print(df.head().to_string())
    return df


app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1(
                        "Comparison of World Bank Country Data",
                        style={"textAlign": "center"},
                    ),
                    html.H5(id="last-fetched-date", style={"textAlign": "center"}),
                    dcc.Graph(id="my-choropleth", figure={}),
                ],
                width=12,
            )
        ),
        dbc.Row([
            dbc.Col(
                [
                    dbc.Label(
                        "Select Data Set:",
                        className="fw-bold",
                        style={"textDecoration": "underline", "fontSize": 20},
                    ),
                    dcc.Dropdown(
                        id="dropdown-indicator",
                        options=[{"label": i, "value": i} for i in indicators.values()],
                        value=list(indicators.values())[0],
                        style={"width": "100%"},
                    ),
                ],
                width=6,
            ),
dbc.Col(
                    [
                        dbc.Label(
                            "Select Years:",
                            className="fw-bold",
                            style={"textDecoration": "underline", "fontSize": 20},
                        ),
                        dcc.RangeSlider(
                            id="years-range",
                            min=2005,
                            max=2016,
                            step=1,
                            value=[2005, 2006],
                            marks={
                                2005: "2005",
                                2006: "'06",
                                2007: "'07",
                                2008: "'08",
                                2009: "'09",
                                2010: "'10",
                                2011: "'11",
                                2012: "'12",
                                2013: "'13",
                                2014: "'14",
                                2015: "'15",
                                2016: "2016",
                            },
                        ),
                        dbc.Button(
                            id="my-button",
                            children="Submit",
                            n_clicks=0,
                            color="primary",
                            className="mt-4 fw-bold",
                        ),
                    ],
                    width=6,
                )

        ]
        ),

        dcc.Store(id="storage", storage_type="session", data={}),
        dcc.Interval(id="timer", interval=1000 * 60, n_intervals=0),
    ]
)


@app.callback(Output("storage", "data"),
              Input("timer", "n_intervals"))
def store_data(n_time):
    dataframe = update_wb_data()
    # Adding last fetched time from imported datetime library
    last_fetched_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #print(last_fetched_time)
    df_records = dataframe.to_dict("records")
    return {"df_records": df_records, "last_fetched_date": last_fetched_date}



@app.callback(
    Output("last-fetched-date", "children"),
    Input("storage", "data"))
def update_last_fetched_date(stored_data):
    if "last_fetched_date" in stored_data:
        return f"Date Last Fetched: {stored_data["last_fetched_date"]}"
    return "Unable to fetch last fetched date from storage"


@app.callback(
    Output("my-choropleth", "figure"),
    Input("my-button", "n_clicks"),
    Input("storage", "data"),
    State("years-range", "value"),
    State("dropdown-indicator", "value"),
)
def update_graph(n_clicks, stored_dataframe, years_chosen, indct_chosen):
    dff = pd.DataFrame.from_records(stored_dataframe["df_records"])
    #print(f"DF from records: {dff.head()}")
    #print(years_chosen)
    #print(indct_chosen)

    if years_chosen[0] != years_chosen[1]:
        dff = dff[dff.year.between(years_chosen[0], years_chosen[1])]
        dff.groupby(["iso3c", "country"])
        #print(dff.head().to_string())
        dff = dff.groupby(["iso3c", "country"])[indct_chosen].mean()
        dff = dff.reset_index()

        fig = px.choropleth(
            data_frame=dff,
            locations="iso3c",
            color=indct_chosen,
            scope="world",
            hover_data={"iso3c": False, "country": True},
            labels={
                indicators["SG.GEN.PARL.ZS"]: "% parliament women",
                indicators["IT.NET.USER.ZS"]: "pop % using internet",
            },
        )
        fig.update_layout(
            geo={"projection": {"type": "natural earth"}},
            margin=dict(l=50, r=50, t=50, b=50),
        )
        return fig

    if years_chosen[0] == years_chosen[1]:
        dff = dff[dff["year"].isin(years_chosen)]
        fig = px.choropleth(
            data_frame=dff,
            locations="iso3c",
            color=indct_chosen,
            scope="world",
            hover_data={"iso3c": False, "country": True},
            labels={
                indicators["SG.GEN.PARL.ZS"]: "% parliament women",
                indicators["IT.NET.USER.ZS"]: "pop % using internet",
            },
        )
        fig.update_layout(
            geo={"projection": {"type": "natural earth"}},
            margin=dict(l=50, r=50, t=50, b=50),
        )
        return fig


if __name__ == "__main__":
    app.run_server(debug=True)
