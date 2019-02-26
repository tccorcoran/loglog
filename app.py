from flask import Flask
from flask import render_template,redirect
from flask_wtf import FlaskForm
from wtforms import StringField,SelectField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
import os
import datetime
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
        utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        pst_now = utc_now.astimezone(pytz.timezone("America/Los_Angeles"))
        cur_time_str = pst_now.strftime("%d %b %y %H:%M")
        print(form.data)
        with open('loglog.log','a') as fi:
            fi.write(f"{cur_time_str},{form.data['blood']},{form.data['size']},{form.data['pain']},{form.data['notes']}\n")
        return redirect('/success')
    return render_template('submit.html', form=form)

@app.route('/success',methods=('GET', 'POST'))
def hi():
    with open ('loglog.log') as fi:
        logs = fi.read()
    logs = logs.split('\n')
    logs = [l.split(',') for l in logs]
    return render_template('success.html', value=logs)

@app.route('/graph',methods=('GET', 'POST'))
def graph():
    import pandas as pd
    import numpy as np
    from bokeh.plotting import figure, output_file, show, save
    from datetime import datetime

    csv = pd.read_csv("loglog.log")
    csv['date'] = csv['date'].apply(lambda x: datetime.strptime(x, "%d %b %y %H:%M"))
    csv['blood'] = csv['blood'].apply(lambda x: {"none": 0, "light": 1,"med":2, "medium": 2, "heavy": 3}[x])
    csv['size'] = csv['size'].apply(lambda x: {"small": 1, "med":2,"medium": 2, "large": 3}[x])
    csv.sort_values(by=['date'], inplace=True, ascending=True)

    # output to static HTML file
    output_file("templates/graph.html", title="Log Log Graph")

    # create a new plot with a a datetime axis type
    p = figure(plot_width=800, plot_height=350, x_axis_type="datetime")


    # add renderers
    p.line(csv['date'], csv['pain'],  color='orange', legend='pain')
    p.line(csv['date'], csv['size'], color='green', legend='size')
    p.line(csv['date'], csv['blood'], color='red', legend='blood')

    # NEW: customize by setting attributes
    p.title.text = "Log Log"
    p.legend.location = "top_left"
    save(p,"templates/graph.html")

    return render_template('graph.html')
    # show the results
    show(p)


# @app.route('/')
# def hello_world():
#     return 'Hello World!'


if __name__ == '__main__':
    app.run()
