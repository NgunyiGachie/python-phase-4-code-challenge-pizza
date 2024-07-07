#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


class Home(Resource):
    def get(self):
        return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = [restaurant.to_dict() for restaurant in Restaurant.query.all()]
        return jsonify(restaurants)


class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

        restaurant_dict = restaurant.to_dict()
        restaurant_pizzas = []
        for restaurant_pizza in restaurant.restaurant_pizzas:
            pizza_dict = {
                "id": restaurant_pizza.id,
                "pizza_id": restaurant_pizza.pizza.id,
                "price": restaurant_pizza.price,
                "restaurant_id": restaurant_pizza.restaurant_id,
                "pizza": {
                    "id": restaurant_pizza.pizza.id,
                    "name": restaurant_pizza.pizza.name,
                    "ingredients": restaurant_pizza.pizza.ingredients,
                },
            }
            restaurant_pizzas.append(pizza_dict)
        restaurant_dict["restaurant_pizzas"] = restaurant_pizzas

        return jsonify(restaurant_dict)

    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            response = make_response(jsonify({"message": "Restaurant deleted"}), 204)
        else:
            response = make_response(jsonify({"error": "Restaurant not found"}), 404)
        return response

class Pizzas(Resource):
    def get(self):
        pizzas = [pizza.to_dict() for pizza in Pizza.query.all()]
        return jsonify(pizzas)


class RestaurantPizzas(Resource):
     
     def post(self):
        data = request.get_json()
        price = data.get("price")
        restaurant_id = data.get("restaurant_id")
        pizza_id = data.get("pizza_id")

        if not (price and restaurant_id and pizza_id):
            return {"error": "Missing required fields"}, 400

        try:
            pizza = Pizza.query.filter_by(id=pizza_id).first()
            restaurant = Restaurant.query.filter_by(id=restaurant_id).first()

            if not (pizza and restaurant):
                return {"error": "Pizza or Restaurant not found"}, 404
            
            new_restaurant_pizza = RestaurantPizza(
                price=price,
                restaurant_id=restaurant_id,
                pizza_id=pizza_id
            )

            db.session.add(new_restaurant_pizza)
            db.session.commit()

            response_data = {
                "id": new_restaurant_pizza.id,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients
                },
                "pizza_id": new_restaurant_pizza.pizza_id,
                "price": new_restaurant_pizza.price,
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address
                },
                "restaurant_id": new_restaurant_pizza.restaurant_id
            }

            return response_data, 201

        except KeyError as e:
            return make_response(jsonify({"errors": [f"Missing key: {str(e)}"]}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"errors": [str(e)]}), 400)
        finally:
            db.session.close()

api.add_resource(Home, "/")
api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantByID, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
