from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Response
import json
import os
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "secret_key_for_flash_messages"

DATA_FILE = "shops_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            try:
                if os.stat(DATA_FILE).st_size == 0:
                    return {}
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

shops = load_data()

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        shop_name = request.form["shop_name"]
        password = request.form["password"]
        if shop_name in shops:
            flash("Shop name already exists. Please choose a different name.")
            return redirect(url_for("signup"))
        shops[shop_name] = {
            "password": password,
            "inventory": {},
            "balance_sheet": {"total_purchase": 0, "total_sales": 0, "profit": 0}
        }
        save_data(shops)
        flash("Shop registered successfully!")
        return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/login", methods=["POST"])
def login():
    shop_name = request.form["shop_name"]
    password = request.form["password"]
    if shop_name in shops and shops[shop_name]["password"] == password:
        return redirect(url_for("inventory", shop_name=shop_name))
    flash("Invalid shop name or password.")
    return redirect(url_for("home"))


@app.route("/inventory/<shop_name>")
def inventory(shop_name):
    if shop_name not in shops:
        flash("Shop not found.")
        return redirect(url_for("home"))
    return render_template("inventory.html", shop_name=shop_name, inventory=shops[shop_name]["inventory"], balance_sheet=shops[shop_name]["balance_sheet"])

# @app.route("/balance_sheet/<shop_name>")
# def balance_sheet(shop_name):
#     if shop_name not in shops:
#         flash("Shop not found.")
#         return redirect(url_for("home"))
#     return render_template("balance_sheet.html", shop_name=shop_name, balance_sheet=shops[shop_name]["balance_sheet"])

@app.route("/add_item/<shop_name>", methods=["GET", "POST"])
def add_item(shop_name):
    if request.method == "POST" and shop_name in shops:
        item_name = request.form["item_name"]
        quantity = int(request.form["quantity"])
        purchase_price = int(request.form["purchase_price"])
        selling_price = int(request.form["selling_price"])

        inventory = shops[shop_name]["inventory"]
        if item_name in inventory:
            inventory[item_name]["quantity"] += quantity
        else:
            inventory[item_name] = {
                "quantity": quantity,
                "purchase_price": purchase_price,
                "selling_price": selling_price
            }
        shops[shop_name]["balance_sheet"]["total_purchase"] += quantity * purchase_price
        save_data(shops)
        flash(f"Item '{item_name}' added/updated successfully!")
        return redirect(url_for("inventory", shop_name=shop_name))
    return render_template("add_item.html", shop_name=shop_name)

@app.route("/sell_item/<shop_name>", methods=["GET", "POST"])
def sell_item(shop_name):
    if request.method == "POST" and shop_name in shops:
        item_name = request.form["item_name"]
        selling_price = int(request.form["selling_price"])
        quantity = int(request.form["quantity"])
        inventory = shops[shop_name]["inventory"]

        if item_name in inventory and quantity <= inventory[item_name]["quantity"]:
            item = inventory[item_name]
            item["quantity"] -= quantity
            sales = quantity * selling_price
            purchase_cost = quantity * item["purchase_price"]
            profit = sales - purchase_cost

            shops[shop_name]["balance_sheet"]["total_sales"] += sales
            shops[shop_name]["balance_sheet"]["profit"] += profit
            save_data(shops)
            flash(f"Sold {quantity} of {item_name}. Profit: {profit}")
        else:
            flash("Insufficient stock or item not found.")
        return redirect(url_for("inventory", shop_name=shop_name))
    return render_template("sell_item.html", shop_name=shop_name, inventory=shops[shop_name]["inventory"])

@app.route("/remove_item/<shop_name>", methods=["POST"])
def remove_item(shop_name):
    if shop_name in shops:
        item_name = request.form["item_name"]
        if item_name in shops[shop_name]["inventory"]:
            del shops[shop_name]["inventory"][item_name]
            save_data(shops)
            flash(f"Item '{item_name}' removed successfully!")
        else:
            flash("Item not found.")
    return redirect(url_for("inventory", shop_name=shop_name))



#from gpt
@app.route("/download_balance_sheet/<shop_name>")
def download_balance_sheet(shop_name):
    # Check if shop exists
    if shop_name not in shops:
        flash("Shop not found.")
        return redirect(url_for("home"))

    # Get the balance sheet data
    balance_sheet = shops[shop_name]["balance_sheet"]

    # Create a CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow(["Total Purchase", "Total Sales", "Profit"])

    # Write balance sheet data
    writer.writerow([balance_sheet["total_purchase"], balance_sheet["total_sales"], balance_sheet["profit"]])

    # Move to the beginning of the StringIO buffer
    output.seek(0)

    # Create a response object with CSV content
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=balance_sheet_{shop_name}.csv"}
    )

if __name__ == "__main__":
    app.run(debug=True)
