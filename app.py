from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import requests
import sys
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
load_dotenv()
API_KEY = os.environ.get('API_KEY')


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


db.create_all()


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        city_name = request.form['city_name']
        city = City(name=city_name)
        try:
            db.session.add(city)
            db.session.commit()
        except IntegrityError:
            flash("The city has already been added to the list!")
        return redirect(url_for('home'))

    city_names = [city for city in db.session.query(City.id, City.name)]
    cities = []
    for _id, name in city_names:
        url = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={name}&appid={API_KEY}&units=metric")
        if url.status_code == 404:
            flash("The city doesn't exist!")
            city = City.query.get(_id)
            db.session.delete(city)
            db.session.commit()
        else:
            r = url.json()
            weather = {"city_id": _id, "city": r["name"], "temp": r["main"]["temp"], "state": r["weather"][0]["main"]}
            cities.append(weather)
    return render_template('index.html', cities=cities)


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.get(city_id)
    db.session.delete(city)
    db.session.commit()
    return redirect(url_for('home'))


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
