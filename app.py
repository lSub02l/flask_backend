import time
import requests
import re

from bson import ObjectId
from flask import Flask, json, jsonify, request, session
from database import db, col_weather
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from utils.regex import psswd_regex, email_regex
from utils.show_json import show_json
from utils.session_expiration import session_expiration

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = "v7854w78883n398292" 
API_KEY = "dc936e5542b904e7e49641cb95179a2f"
now = datetime.now()   
app.permanent_session_lifetime = timedelta(minutes=1)

#   App functions
def fixed_temp(x):
    x = round(x - 273.15, 2)
    return x

def get_weather():
    response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q=Warsaw&appid={API_KEY}')
    data = response.json()
    db.weather.insert_one({
        "temp": fixed_temp(data['main']['temp']),
        "min_temp": fixed_temp(data['main']['temp_min']),
        "max_temp": fixed_temp(data['main']['temp_max']),
        "feels_like": fixed_temp(data['main']['feels_like']),
        "humidity": data['main']['humidity'],
        "pressure": data['main']['pressure'],
        "description": data['weather'][0]['description'],
        "time":time.strftime("%H:%M"),
        "date":time.strftime("%-%m-%Y"),
        "city": data['name']
    }) 

#   Routes 
@app.route("/create-travel", methods=["GET","POST"])
def create_travel():
    title = request.json["title"]
    price = request.json["price"]
    country = request.json["country"]
    desc = request.json["desc"]
    image = request.json["image"]

    travel_exists = db.travels.find_one({"title":title})
    if travel_exists:
        return show_json("Wycieczka o podanej nazwie juz istnieje", 405, False)

    db.travels.insert_one({
        "title":title,
        "price":price,
        "country":country,
        "desc":desc,
        "image":image
    })

    return show_json("Udalo sie dodac nowa wycieczke", 200, True)

@app.route("/all-travels")
def all_travels():
    data = db.travels.find({})
    travels = []
    for item in data:
       item['_id'] = str(item['_id'])
       travels.append(item)
    print(travels)
    return show_json("Udało się pobrać dane",200,True, travels) 

@app.route("/single-travel/<id>")
def single_travel(id):
    try:
        travel = list(db.travels.find({"_id":ObjectId(id)}))[0]
        travel["_id"] = str(travel['_id'])
        return show_json("Udalo sie znalezc wycieczke", 200, True, travel)
    except Exception as e:
        print(str(e))
        return show_json("Nie udalo sie znalezc wycieczki", 404, False)
    
@app.route("/edit-travel/<id>", methods=["PUT"])
def edit_travel(id):
    try:
        travel_json = request.json
        travel = db.travels.update_one({"_id":ObjectId(id)},{"$set":travel_json})
        if travel.modified_count == 1:
            return show_json("Zaktualizowano", 200, True)
        else:
            return show_json("Nie odnaleziono wycieczki", 404, False)
    except Exception as e:
        print(str(e))
        return show_json("Nie odnaleziono wycieczki", 404, False) 
    
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

#   Weather functions

# def get_weather(city):
#     response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}")
#     print(response)
    
#     if response.ok:
#         data = response.json()
#         insert_to_weather = col_weather.insert_one({
#             "city":data['name'],
#             "time":now.strftime("%H:%M:%S"),
#             "date":now.strftime("%d:%m:%y"),
#             "temp":data['main']['temp'],
#             "description":data['weather'][0]['description'],
#             "temp_min":data['main']['temp_min'],
#             "temp_max":data['main']['temp_max'],
#             "feels_like":data['main']['feels_like'],
#             "humidity":data['main']['humidity'],
#             "pressure":data['main']['pressure']
#         })

# @app.route("/weather/<city>")
# def show_weather(city):
#     get_weather(city)
#     response1 = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}")
#     open('last_cities.txt').read()
#     open('last_cities.txt', 'a').write(city + ",")

#     print(response1)
#     if response1.ok:
#         city_data = response1.json()
#         try:
#             city_data = db.weather.find({}).sort({"_id":-1})
#             weather = []
#             for item in city_data:
#                 item['_id'] = str(item['_id'])
#                 weather.append(item)
#                 print(weather)
#                 return show_json("Udało się pobrać dane",200,True, weather)
        
#         except Exception as e:
#             print(str(e))
#             return show_json("Nie udało się pobrac danych pogodowych", 500, False)

@app.route("/show-weather")
def show_weather():
     data = db.weather.find({})
     weather = []
     for item in data:
        item['_id'] = str(item['_id'])
        weather.append(item)

     return show_json("Udało się pobrać dane",200,True,weather) 

#   Register
@app.route("/register", methods=["POST"])
def register():
    username = request.json['username']
    email = request.json['email']
    psswd = request.json['psswd']
    hashed_psswd = generate_password_hash(psswd)

    if db.users.find_one({"username":username}):
        return show_json("Uzytkownik o podanej nazwie juz istnieje", 400, False)
    if db.users.find_one({"email":email}):
        return show_json("Email jest juz w uzyciu", 400, False)
    if re.match(email_regex, email) is None:
        return show_json("Podaj poprawny adres email", 400, False)
    if re.match(psswd_regex, psswd) is None:
        return show_json("Haslo musi zawierac mala, duza litere,cyfre, minimum 8 znakow i znak specjanlny", 400, False)

    new_user = {
        "username":username,
        "email":email,
        "psswd":hashed_psswd
    }

    db.users.insert_one(new_user)
    new_user['_id'] = str(new_user['_id'] )
    return show_json("Utworzono konto", 201, True, new_user)

#   Login
@app.route("/login", methods = ["POST"])
def login(): 
    psswd = request.json['psswd']
    email = request.json['email']

    user_exists = db.users.find_one({'email':email})

    if user_exists is None:
        return show_json("Bledny adres email", 404, False)

    psswd_check = check_password_hash(user_exists['psswd'], psswd)

    if psswd_check == False:
        return show_json("Bledne haslo", 404, False)
    
    expiration = session_expiration(app)
    session['email'] = email
    session['date'] = (datetime.now() + expiration).strftime("%H:%M:%S")
    return show_json("Poprawnie zalogowano na konto", 200, True, email)

@app.route("/whoami")
def who_am_i():
    if "email" in session:
        user = session['email']
        return show_json("Informacje o uzytkowniku", 200, True, user)
    else:
        return show_json("Odmowa dostepu", 401, False)
    
@app.route("/logout")
def logout():
    session.pop('email', None)
    
    return show_json("Pomyslnie wylogowano", 200, True)