from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import datetime


app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["stock_watcher"]
collection = db["stocks"]

client =MongoClient("mongodb://localhost:27017/")
db = client["stock_watcher"]
user_collection = db["users"]


def get_daily_data(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


@app.route("/daily_data/<string:name>")
def daily_data(name):
    api_key = "Z3K8UMJIFK8W7511"
    data = get_daily_data(name, api_key)
    if "Time Series (Daily)" not in data:
        print("Invalid company name")
        return jsonify({"status": "Failed to retrieve data"})

    else:

        symbol = data["Meta Data"]["2. Symbol"]
        daily_data = data["Time Series (Daily)"]
        one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        one_month_ago = one_month_ago.strftime("%Y-%m-%d")
        filtered_daily_data = {k: v for k, v in daily_data.items() if k >= one_month_ago}
        document = {
            "Symbol": symbol,
            "Daily Data":filtered_daily_data
}      
        collection.insert_one(document)
        return jsonify({"status": "Data stored successfully"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    mob=data["mobile"]
    email = data["email"]
    password = data["password"]
    
    user = {
        "username": username,
        "email": email,
        "password": password,
        "mobile":mob
    }
    
    user_collection.insert_one(user)
    
    return jsonify({"message": "User registered successfully"}), 201




@app.route("/company/<string:name>")
def get_company_data(name):
   
    company = collection.find_one({"Symbol": name})
    if company:
        company["_id"] = str(company["_id"])
        return jsonify(company), 200
    else:
        return jsonify({"error": "No data found for the given company name."})

@app.route("/daily_data/<string:symbol>/<string:date>", methods=["GET"])
def get_data(symbol, date):
    data = request.get_json()
    mob=data["mobile"]
    

    user=user_collection.find_one({'mobile':mob})
    if user:

   
        document = collection.find_one({"Symbol": symbol, "Daily Data." + date: {"$exists": True}})

    
        if not document:
            return jsonify({"error": "Not found"}), 404

        daily_data = document["Daily Data"][date]
        sd={
            "$set":{ "Search":{

                "Symbol":document["Symbol"],

                "Open": daily_data["1. open"],
                "Close": daily_data["4. close"],
                "High": daily_data["2. high"],
                "Low": daily_data["3. low"]
                }
            }

        }

        user_collection.update_one(user,sd)

    
        return jsonify({
            "Open": daily_data["1. open"],
            "Close": daily_data["4. close"],
            "High": daily_data["2. high"],
            "Low": daily_data["3. low"],
        })

    else:
        return jsonify({"message":"You're not an existing user"})


if __name__ == "__main__":
    app.run(debug=True)
