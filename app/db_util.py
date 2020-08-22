import click
import datetime

from flask import current_app, g
from flask.cli import with_appcontext
from app.model import House
import datetime
import pandas as pd

from folium import FeatureGroup, LayerControl, Map, Marker
from folium.features import DivIcon

import branca.colormap as cm
import numpy as np

from app import scrape
from app import db

import plotly.graph_objs as go
import plotly
import os 

filename = "scrape.csv"
historical_data = "hist_data.csv"

map_file = "app/templates/map.html"
hist_file = "app/templates/hist.html"

def create_map(result):

    row = next(result.iterrows())[1]

    m = Map(
        location=[row.latitude, row.longitude],
        zoom_start=13,
        tiles='Stamen Terrain'
    )

    feature_group = FeatureGroup(name='Some icons')

    for index, row in result.iterrows():
        x = "not planned"
        if str(row.openHouse)!="nan":
            x =datetime.datetime.strptime(row.openHouse,"%Y-%m-%dT%H:%M:%S.000z")
            x =x.strftime('%b %d %Y %H:%M:%S')
        Marker(location=[row.latitude, row.longitude],
                      icon=DivIcon(
                          icon_size=(150,36),
                          icon_anchor=(7,20),
                          html = '<strong style="text-shadow:-1px -1px 0 #000,1px -1px 0 #000,-1px 1px 0 #000,1px 1px 0 #000;">'+
                          '<font size="4" color="'+row['color']+'">'+str(round(row['milprice'],2))+'</>'
                      ),
                      popup=f"<h4>{row.street}</> <br> "+
                           f"<h4> Size: {str(row['size'])} m<sup>2</sup> </> <br> "+
                           f"<h4> Rooms: {str(int(row.rooms))} </> <br> "+
                           f"<h4> Floor: {str(row.floor)}</> <br> "+
                           f"<h4> Expense: {str(row.expense)}</> <br> "+
                           f"<h4> Change: -{str(row.priceChangePercentTotal)}% </> <br> "+
                           f"<a class='btn-floating btn-large waves-effect waves-light red'"+
                           f"href='add/{row.guid}'>"+
                           "<i class='material-icons'>add</i></a> <br>"+
                           f"<h4> Open House: {x} </> <br> "+
                           f"<a href='{row.url}' target='_blank'>link</a>"

              )\
                      .add_to(feature_group)

    feature_group.add_to(m)
    LayerControl().add_to(m)
    m.save(map_file)

def init_db_and_html(db):
    
    db.drop_all()
    db.create_all()

    houses = pd.read_csv(filename)

    def colormapper(x):
        return str(linear(x))

    def rand_jitter(arr):
        stdev = .000001*(max(arr)-min(arr))
        return arr + np.random.randn(len(arr)) * stdev

    houses["latitude"] = rand_jitter(houses['latitude'])
    houses["longitude"] = rand_jitter(houses['longitude'])
    houses["milprice"] = houses["price"] / 1e6

    linear = cm.LinearColormap(
        ['green', 'yellow', 'red'],
        vmin=houses.milprice.min(), vmax=houses.milprice.max()
    )

    houses["color"] = houses["milprice"].apply(colormapper)
    houses["url"] = ["https://www.boliga.dk/bolig/" + str(i) for i in houses.id.values]
    houses = houses[~houses["guid"].isnull()]

    create_map(houses)
    
    hist = pd.read_csv(historical_data)
    create_hist_plot(hist)
    
    for index, row in houses.iterrows():

        house = House(
        guid=row['guid'],
        price=round(row['milprice'],2),
        size=row['size'],
        expense = row.expense,
        address = row.street,
        link = row.url,
        favorite = False,
        )

        db.session.add(house)

    db.session.commit()

def price_time(df):
    time_frame = df[['Date',"sqmPrice",'area']].sort_values("Date")
    time_frame=time_frame.groupby("Date").agg({'sqmPrice':["mean"]})
    #, 'counting':["mean"]}
    time_frame=time_frame.reset_index()
    time_frame=time_frame.set_index("Date")
    time_frame['MA'] = time_frame.rolling(window=44).mean()
    return time_frame

def create_hist_plot(houses):
    fig = go.Figure()
    t1 = price_time(houses.query("area!='FRB'"))
    t2 = price_time(houses.query("area=='FRB'"))
    t3 = price_time(houses)

    for t,name in zip([t1,t2,t3], ["KbhK","FRB","Both"]):

        fig.add_trace(go.Scatter(
                        x=t.index,
                        y=t['MA'],
                        name=name,
                        opacity=0.8))
    fig.write_html(hist_file)
    # with open(hist_file, 'w') as f:

    #     plotly.offline.plot(fig, filename=f)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db_and_html(db)
    click.echo('Initialized the database.')

@click.command('process')
@with_appcontext
def tranform_command():
    """
    My filters
    """
    houses = pd.read_csv(filename)
    
    houses.drop_duplicates(inplace=True)
    houses=houses.rename({"exp":"expense", "address":"street","squaremeterPrice":"sqmPrice"}, axis=1)
    houses=houses.query("expense<6000 and size > 80 and zipCode < 2001 and propertyType!=5 and price < 6000000")
    houses = houses[~houses.street.str.contains("Roskildevej")]
    houses = houses[~houses.street.str.contains("Rådmand")]
        
    houses['Date'] = pd.to_datetime(houses.createdDate)
    houses.to_csv(filename, index=False)
    

@click.command('scrape')
@with_appcontext
def scrape_command():
    """Clear the existing data and create new tables."""
    click.echo('Starting scrape.')
    scrape\
        .get_current_sales(loop_range=range(1,25),zip_range=[1000,2001])\
        .to_csv(filename, index=False)
    click.echo('Done!')
    

@click.command('scrape_hist')
@with_appcontext
def scrape_hist_command():
    """Clear the existing data and create new tables."""
    click.echo('Starting scrape.')
    houses = scrape\
        .get_historic_sales(loop_range=range(1,500),zip_range=[1000,2001])\
        .drop_duplicates()
    print(houses.shape)
    houses.rename(
        {"exp":"expense", "address":"street","squaremeterPrice":"sqmPrice"},
        axis=1,
        inplace=True
        )
   
    houses["area"] = ['FRB' if x >= 1800 else 'kbhK' for x in houses['zipCode']]
    houses['floor']=houses.street.str.extract(r', (\d|ST|st|St|kld|KLD|Kld)', expand=True)
    houses['Date'] = pd.to_datetime(houses.soldDate)
    houses=houses.query("saleType=='Alm. Salg'")\
        .query("sqmPrice<200000")\
        .query('sqmPrice>3000')
    
    houses.to_csv(historical_data, index=False)

    click.echo('Done!')