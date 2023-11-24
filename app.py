from bson import ObjectId
from flask import Flask, render_template, request, jsonify, json, session
from database import db, weather
from utils.show_json import show_json
from flask_cors import CORS
import requests,time
import threading
from werkzeug.security import generate_password_hash, check_password_hash
import re
from utils.regex import password_regex, email_regex
from utils.session_expiration import session_expiration
from datetime import datetime, timedelta

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.secret_key = 'kd5u9823h4u12b412uib49123241j'
app.permanent_session_lifetime = timedelta(minutes=1)


@app.route("/create-travel", methods=["GET", "POST"])
def create_travel():
    if 'email' in session:
        title = request.json["title"]
        price = request.json["price"]
        country = request.json["country"]
        desc = request.json["desc"]
        image = request.json["image"]

        travel_exists = db.travels.find_one({"title":title}) #search for copy

        if travel_exists:
            return show_json("Wycieczka o podanej nazwie już istnieje", 405, False) 

        db.travels.insert_one({
            "title": title,
            "price": price,
            "country": country,
            "desc": desc, 
            "image": image
        })

        return show_json("Udało się dodać nową wycieczkę", 200, True)
    else:
        return show_json("Odmowa dostępu", False)
@app.route("/all-travels")
def all_travels():
     data = db.travels.find({})
     travels = []
     for item in data:
        item['_id'] = str(item['_id'])
        travels.append(item)

     return show_json("Udało się pobrać dane",200,True,travels)

@app.route("/single-travel/<id>")
def single_travel(id):  
    try:
        travel = list(db.travels.find({"_id":ObjectId(id)}))[0]

        travel["_id"] = str(travel["_id"])
        return show_json("Udało się wybrać kraj", 200, True, travel)
    except Exception as e:   
        print(str(e))
        return show_json("Nie udało się znaleźć wybranego kraju", 404, False)
    
@app.route("/edit-travel/<id>", methods=["PUT"])
def edit_travel(id):
    try:
        travel_json = request.json
        travel = db.travels.update_one({"_id":ObjectId(id)},{"$set":travel_json})

        if travel.modified_count == 1:
            return show_json("Zaktualizowano plik", 200, True)
        else:
            return show_json("Nie odnaleziono wycieczki", 404, False)
    except Exception as e:
        print(str(e))
        return show_json("Nie znaleziono wycieczki", 404, False)

@app.route("/delete-travel/<id>", methods=["DELETE"])
def delete_travel(id):
    try:
        result = db.travels.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 1:
            return show_json("Pomyślnie usunięto wycieczke", 200, True)
        return show_json("Nie odnaleziono wycieczki", 404, False)
    except Exception as e:
        print(str(e))
        return show_json("Nie udało się usunąć wycieczki", 500, False)

def napraw_temp(x):
    x = round(x - 273.15, 2)
    return x

def weather_data():
    print('Pobieram dane')
    response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q=Warsaw&appid=912c622485ebcccfe6e75ebb3dc2de10')
    data = response.json()
    db.weather.insert_one({
        "temp": napraw_temp(data['main']['temp']),
        "min_temp": napraw_temp(data['main']['temp_min']),
        "max_temp": napraw_temp(data['main']['temp_max']),
        "feels_like": napraw_temp(data['main']['feels_like']),
        "humidity": data['main']['humidity'],
        "pressure": data['main']['pressure'],
        "description": data['weather'][0]['description'],
        "time":time.strftime("%H-%M"),
        "date":time.strftime("%d-%m-%Y"),
        "city": data['name']
    })

@app.route("/show-weather")
def show_weather():
     data = db.weather.find({})
     weather = []
     for item in data:
        item['_id'] = str(item['_id'])
        weather.append(item)

     return show_json("Udało się pobrać dane",200,True,weather) 

#register
@app.route("/register", methods=["POST"])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    hashed_password = generate_password_hash(password)

    if db.users.find_one({"username":username}):
        return show_json("Użytkownik o podanej nazwie już istnieje", 400, False)
    
    if db.users.find_one({"email": email}):
        return show_json("Email został już użyty", 400, False)

    if re.match(password_regex, password) is None:
        return show_json("Hasło musi zawierać mała, dużą literę, cyfrę, minimum 8 znaków i znak specjalny", 400, False)
    
    if re.match(email_regex, email) is None:
        return show_json("Podaj poprawny adres email", 400, False)

    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password
    }

    db.users.insert_one(new_user)
    new_user['_id'] = str(new_user['_id'])

    return show_json("Utworzono konto", 201, True, new_user)

#login
@app.route("/login", methods=["POST"])
def login():
    password = request.json['password']
    email = request.json['email']

    user_exists = db.users.find_one({"email": email})

    if user_exists is None:
        return show_json("Błędny adres email", 404, False)
    
    password_check = check_password_hash(user_exists['password'], password)

    if password_check == False:
        return show_json("Niepoprawne hasło", "404", False)
    
    expiration = session_expiration(app)
    session['email'] = email
    session['date'] = (datetime.now() + expiration).strftime("%H:%M:%S")
    return show_json("Poprawnie zalogowano", 200, True, email)

@app.route("/whoami")
def who_am_i():
    if "email" in session:
        user = session['email']
        return show_json("Informacje o użytkowniku", 200, True)
    else:
        return show_json("Odmowa dostępu", 401, False)

#logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    return show_json("Pomyślnie wylogowano", 200, True)

















#schedule.every(5).minutes.do(weather_data)

# while True:
#     schedule.run_pending()
#     time.sleep(1)

# def download_weather_data():
#     weather_data()
#     threading.Timer(600.0, download_weather_data).start()

# download_weather_data()

# @app.route("/data/<id>", methods=["GET", "POST"])
# def data(id):

