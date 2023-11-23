from bson import ObjectId
from flask import Flask, render_template, request, jsonify, json
from database import db
from utils.show_json import show_json
from flask_cors import CORS

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/create-travel", methods=["GET", "POST"])
def create_travel():
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
