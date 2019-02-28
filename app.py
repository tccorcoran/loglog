from flask import Flask
from flask import render_template,redirect
from flask_wtf import FlaskForm
from wtforms import StringField,SelectField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
import pandas as pd
import numpy as np
from datetime import datetime
from bokeh.plotting import figure, output_file, show, save
from bokeh.layouts import column

from bokeh.models.formatters import DatetimeTickFormatter
import os
import pytz

SECRET_KEY = os.urandom(32)
from pdb import set_trace
class MyForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])

class MyForm(FlaskForm):
    blood = SelectField(u'Blood', choices=[('none', 'None'), ('light', 'Light'), ('medium', 'Medium'),('heavy', 'Heavy')])
    size = SelectField(u'Size', choices=[('small', 'Small'), ('med', 'Medium'),("large",'Large')])
    pain = SelectField(u'Pain', choices=[(str(i),str(i)) for i in range(0,11)])
    notes = StringField(label="Notes")

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/', methods=('GET', 'POST'))
def submit():
    form = MyForm()
    if form.validate_on_submit():
        utc_now = pytz.utc.localize(datetime.utcnow())
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        cur_time_str = pst_now.strftime("%d %b %y %H:%M")
        with open('loglog.log','a') as fi:
            fi.write(f"{cur_time_str},{form.data['blood']},{form.data['size']},{form.data['pain']},{form.data['notes']}\n")
        csv = dataframeize("loglog.log")
        csv['by_day'] = csv['date'].apply(lambda x: x.strftime("%b %d"))
        grouped = csv.groupby("by_day")
        df = grouped.agg({"date": len, "blood": np.mean, "pain": np.mean, "size": np.mean}).rename(
            columns={'date': 'count'})
        df.to_csv("loglog_agg.log")
        return redirect('/success')
    return render_template('submit.html', form=form)

def maybe_round(val):
    try:
        val = float(val)
        val = "{:.1f}".format(val)
    except ValueError:
        val = val
    return  val

@app.route('/success',methods=('GET', 'POST'))
def hi():
    with open ('loglog.log') as fi:
        logs = fi.read()
    logs = logs.split('\n')
    logs = [l.split(',') for l in logs]
    with open('loglog_agg.log') as fi:
        day_agg = fi.read()
    day_agg = day_agg.split('\n')
    day_agg = [list(map(maybe_round,l.split(','))) for l in day_agg[1:]]
    return render_template('success.html', value=logs, daily=day_agg)

def dataframeize(log_path):
    csv = pd.read_csv("loglog.log")
    csv['date'] = csv['date'].apply(lambda x: datetime.strptime(x, "%d %b %y %H:%M"))
    csv['blood'] = csv['blood'].apply(lambda x: {"none": 0, "light": 1,"med":2, "medium": 2, "heavy": 3}[x])
    csv['size'] = csv['size'].apply(lambda x: {"small": 1, "med":2,"medium": 2, "large": 3}[x])
    csv.sort_values(by=['date'], inplace=True, ascending=True)
    return csv

@app.route('/graph',methods=('GET', 'POST'))
def graph():

    csv = dataframeize("loglog.log")
    daily_agg = pd.read_csv("loglog_agg.log")
    daily_agg['by_day'] = daily_agg['by_day'].apply(lambda x: datetime.strptime(x, "%b %d"))
    # output to static HTML file
    output_file("templates/graph.html", title="Log Log Graph")

    # create a new plot with a a datetime axis type
    p = figure(plot_width=800, plot_height=350, x_axis_type="datetime")
    p2 = figure(plot_width=800, plot_height=350,x_axis_type="datetime")

    p2.line( daily_agg['by_day'], daily_agg['count'])

    # add renderers
    p.line(csv['date'], csv['pain'],  color='orange', legend='pain')
    p.line(csv['date'], csv['size'], color='green', legend='size')
    p.line(csv['date'], csv['blood'], color='red', legend='blood')

    # NEW: customize by setting attributes
    p.xaxis.formatter = DatetimeTickFormatter(days="%d-%b-%Y", hours="%H:%M", seconds="%S")
    p.title.text = "BM Log"
    p2.title.text = "BM Count"
    p.legend.location = "top_left"
    p2.xaxis.formatter = DatetimeTickFormatter(days="%d-%b")

    save(column(p,p2),"templates/graph.html")

    return render_template('graph.html')



if __name__ == '__main__':
    app.run()
