from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json
import uuid
import time

# Connect to our local MongoDB
client = MongoClient('mongodb://localhost:27017/')
# Choose database
db = client['InfoSys']
# Choose collections
users = db['Users']
products = db['Products']

# Initiate Flask App
app = Flask(__name__)

def has_required_fields(field_names, data):
    # Σε αυτήν την συνάρτηση βάζουμε σε list τα ονόματα των fields που πρέπει να περιέχει το json που θα δώσει ο χρήστης.
    # Αν δεν υπάρχει κάποιο από αυτά, επιστρέφεται False
    for field in field_names:
        if not field in data:
            return False
    return True

users_sessions = list()
def create_session(email, category):
    # Η συνάρτηση αυτή δημιουργεί και επιστρέφει ένα μοναδικό κωδικό uuid
    user_uuid = str(uuid.uuid1())
    users_sessions.append((user_uuid, email, time.time(), category))
    return user_uuid

def is_session_valid(user_uuid, category):
    # Η συνάρτηση αυτή ελέγχει αν το uuid είναι έγκυρο και αν ο χρήστης που του ανήκει, έχει πρόσβαση στο category
    # Είναι έτσι σχεδιασμένο που αν ο χρήστης είναι admin μπορεί να έχει προσβάση στα endpoint που είναι Simple ενώ το αντίθετο δεν ισχύει
    for session in users_sessions:
        if (session[0] == user_uuid) and (session[3]==category or session[3]=="Admin"):
            return True
    return False

@app.route('/createUser', methods=['POST'])
def create_user():
    # Το endpoint αυτό δημιουργεί καινούργιο χρήστη
    try:
        data = json.loads(request.data)
    except Exception:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("email","username","password"),data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    # Έλεγχος αν το email χρησιμοποιείται από άλλον χρήστη
    if users.find({"email":data['email']}).count() == 0 :
        users.insert_one({"name":data["username"],"email":data["email"],"password":data["password"],"category":"Simple","orderHistory":""})
        # Μήνυμα επιτυχίας
        return Response(data['username'] + " was added to the MongoDB", mimetype='application/json', status=200)
    else:
        # Διαφορετικά, αν υπάρχει ήδη κάποιος χρήστης με αυτό το email.
        return Response("A user with the given email already exists", mimetype='application/json', status=400)

@app.route('/login', methods=['POST'])
def login():
    # Το endpoint αυτό χρησιμοποιείται για να συνδεθεί ο χρήστης
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("email", "password"), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    # Έλεγχος αν υπάρχει κάποιος χρήστης με αυτό το email και τον κωδικό
    user = users.find_one({ "$and": [{"email":data['email']},{"password":data['password']}]})
    if user is None:
        # Η αυθεντικοποίηση είναι ανεπιτυχής. Μήνυμα λάθους (Λάθος email ή password)
        return Response("Wrong email or password.", mimetype='application/json', status=400)
    else:
        # Επιτυχής ταυτοποίηση. Επιστροφή uuid
        res = {"uuid": create_session(user['email'],user['category']), "username":user['name']}
        return Response(json.dumps(res), mimetype='application/json', status=200)

@app.route('/searchBy_name', methods=['GET'])
def searchBy_name():
    # Αυτό το endpoint επιστρέφει τα προϊόντα με αυτό το name
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("name",), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'],"Simple"):
        temp_products = products.find({"name":data["name"]})
        if temp_products is None:
            # Δεν υπάρχουν προϊόντα με αυτό το όνομα
            return Response("There isn't any product with this name", mimetype='application/json', status=400)
        else:
            return Response(json.dumps(temp_products), mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

@app.route('/searchBy_category', methods=['GET'])
def searchBy_category():
    # Αυτό το endpoint επιστρέφει τα προϊόντα με αυτό το category
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("category",), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'],"Simple"):
        temp_products = products.find({"category":data["category"]})
        if temp_products is None:
            # Δεν υπάρχουν προϊόντα με αυτό το category
            return Response("There isn't any product with this category", mimetype='application/json', status=400)
        else:
            return Response(json.dumps(temp_products), mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

@app.route('/searchBy_ID', methods=['GET'])
def searchBy_ID():
    # Αυτό το endpoint επιστρέφει τα προϊόντα με αυτό το id
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("id",), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'],"Simple"):
        product = products.find_one({"_id" : ObjectId(data["id"])})
        if product is None:
            # Δεν υπάρχουν προϊόντα με αυτό το id
            return Response("There isn't any product with this id", mimetype='application/json', status=400)
        else:
            return Response(json.dumps(product), mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

cart_products="{" # Αυτό το string θα είναι σε μορφή JSON και θα κρατάει τα id των προϊόντων που είναι μέσα στο καλάθι
# Για παράδειγμα αν έχουμε 2 προϊόντα με id = 0 και 1 αντίστοιχα το String αυτό θα είναι: {"product_1":"0","product_2":"1",
# Οπότε για να το μετατρέψουμε σε JSON αρκεί να του αφαιρέσουμε την τελευταία τιμή και προσθέσουμε στο τέλος ένα }
# Για την αρίθμηση των προϊόντων μας βοηθάει η μεταβλητή cart_items που θα δούμε πιο κάτω. Αριθμούνται έτσι καθώς αν είχαν το ίδιο name θα υπήρχε πρόβλημα κατά την μετατροπή του String σε JSON
cart_total_price=0 # Εδώ αποθηκεύται η συνολική τιμή των προϊόντων που είναι μέσα στο καλάθι
cart_items=0 # Ο αριθμός αυτός δείχνει πόσα προϊόντα έχει το καλάθι.
@app.route('/addTo_cart', methods=['GET'])
def addTo_cart():
    # Αυτό το endpoint προσθέτει στο καλάθι το προϊόν με το id που δίνει ο χρήστης
    # Ζητείται και quantity καθώς μπορεί να θέλει να προσθέσει ένα προϊόν πάνω από μια φορά
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("id","quantity"), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'], "Simple"):
        product = products.find_one({"_id" : ObjectId(data["id"])})
        if product is None:
            # Δεν υπάρχει προϊόν με αυτό το id
            return Response("There isn't any product with this id", mimetype='application/json', status=400)
        elif product["stock"]<data["quantity"]:
            # Το stock δεν επαρκεί για την παραγγελία
            return Response("There aren't so many items in stock", mimetype='application/json', status=402)
        else:
            # Πέρασαν όλοι οι έλεγχοι οπότε πρέπει να προστεθεί στο καλάθι
            global cart_products, cart_total_price, cart_items
            # Πρακτικά όταν ο χρήστης επιλέγει n ποσότητα από ένα προϊόν, το προϊόν αυτό προστίθεται n φορές στο καλάθι
            for i in range(0,data["quantity"]):
                cart_items+=1
                cart_products+="\"product_"+str(cart_items)+"\" : \""+str(product["_id"])+"\","
                cart_total_price+= product["price"]
            return show_cart()
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

@app.route('/show_cart', methods=['GET'])
def show_cart():
    # Αυτό το endpoint χρησιμοποιείται για να επιστρέφει το καλάθι μαζί με την συνολική τιμή (σε JSON μορφή)
    if is_session_valid(request.headers['authorization'], "Simple"):
        global cart_products, cart_total_price, cart_items
        if cart_items==0:
            return Response("Cart is empty", mimetype='application/json', status=200)
        else:
            return Response(json.dumps(cart_products[:-1] + ", \"total_price\":" + str(cart_total_price) + "}"),
                        mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

@app.route('/deleteItem_cart', methods=['GET'])
def deleteItem_cart():
    # Αυτό το endpoint διαγράφει το id από το καλάθι του χρήστη (Σημείωση: Αν υπάρχουν 2+ προϊόντα με αυτό το id διαγράφεται μόνο το 1)
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("id",), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'], "Simple"):
        global cart_products, cart_total_price, cart_items
        cart_products = json.loads(cart_products[:-1]+"}") # Μετατρέπουμε το καλάθι σε JSON

        deleted = False # Αυτή η μεταβλητή την χρησιμοποιούμε σαν flag
        for i in range(1,cart_items+1):
            # Έλεγχος για το id
            if cart_products['product_'+str(i)] == data["id"]:
                del cart_products['product_'+str(i)]
                cart_total_price -= products.find_one({"_id" : ObjectId(data["id"])})["price"]
                deleted=True
                break
        if not deleted:
            # Δεν υπάρχει το id στο καλάθι
            cart_products = json.dumps(cart_products)[:-1] + "," # Μετατρέπουμε το JSON σε String
            return Response("There isn't any product with this id in cart", mimetype='application/json', status=400)
        else:
            # Εφόσον έχει γίνει η διαγραφή θα υπάρχει κενό στους αριθμούς των προϊόντων οπότε πρέπει να διορθωθεί
            # πχ αν είχαμε 3 προϊόντα με id 0, 1, 2 αντίστοιχα το καλάθι θα ήταν {"product_1":"0","product_2":"1","product_3":"2",
            # Αν ο χρήστης διέγραφε το id 1 τότε το καλάθι θα ήταν {"product_1":"0","product_3":"2", οπότε θα πρέπει το κενό αυτό να διορθωθεί και να γίνει {"product_1":"0","product_2":"2",
            new_cart_products="{" # Ξαναχτίζεται το καλάθι από την αρχή
            new_cart_items = 0
            for i in range(1, cart_items + 1):
                if 'product_'+str(i) in cart_products:
                    new_cart_items += 1
                    print("5: ",type(cart_products['product_'+str(i)]))
                    new_cart_products += "\"product_" + str(new_cart_items) + "\" : \"" + cart_products['product_'+str(i)] + "\","
            cart_products = new_cart_products
            cart_items = new_cart_items
            return show_cart()
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

@app.route('/buyProducts_cart', methods=['GET'])
def buyProducts_cart():
    # Το endpoint αυτό κάνει την αγορά των προϊόντων
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("card_number",), data):
        return Response("Information incomplete", status=500, mimetype="application/json")
    if not len(data["card_number"]) == 16:
        return Response("Card number has to be 16-numbers long", mimetype='application/json', status=400)

    if is_session_valid(request.headers['authorization'], "Simple"):
        global cart_products, cart_total_price, cart_items,users_sessions
        receipt = cart_products[:-1] + ", \"total_price\":" + str(cart_total_price) + "},"
        for session in users_sessions:
            if session[0] == request.headers['authorization']:
                users.find_one_and_update({"email" : session[1]},{"$set":{"orderHistory" : users.find_one({"email" : session[1]})["orderHistory"]+ receipt}})
                # Εφόσον έγινε η αγορά το καλάθι αδειάζει
                cart_products="{"
                cart_total_price=0
                cart_items=0
                break
        return Response(receipt, mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=401)

@app.route('/show_history', methods=['GET'])
def show_history():
    # Το endpoint αυτό δείχνει το ιστορικό του χρήστη
    global users_sessions
    if is_session_valid(request.headers['authorization'], "Simple"):
        for session in users_sessions:
            if session[0] == request.headers['authorization']:
                return Response(json.dumps(users.find_one({"email" : session[1]})["orderHistory"]), mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=400)

@app.route('/delete_user', methods=['GET'])
def delete_user():
    # Το endpoint αυτό διαγράφει τον ίδιο τον χρήστη που το κάλεσε
    global users_sessions
    if is_session_valid(request.headers['authorization'], "Simple"):
        for session in users_sessions:
            if session[0] == request.headers['authorization']:
                users.find_one_and_delete({"email": session[1]})
                while True:
                    clean = True
                    for i in range(0,len(users_sessions)):
                        if (users_sessions[i])[1]==session[1]:
                            users_sessions.pop(i)
                            clean=False
                            break
                    if clean:
                        break
                return Response("Successful user deletion",mimetype='application/json', status=200)
    else:
        return Response("This action requires login", mimetype='application/json', status=400)

@app.route('/createProduct', methods=['GET'])
def create_product():
    # Δημιουργία προϊόντος
    # Το endpoint αυτό όπως και τα υπόλοιπα που ακουλουθούν χρειάζονται admin rights
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not ("name" in data) or not ("price" in data) or not ("description" in data) or not ("category" in data) or not ("stock" in data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'],"Admin"):
        products.insert_one({"name":data["name"],"price":float(data["price"]),"description":data["description"],"category":data["category"],"stock":data["stock"]})
        return Response("Product "+data['name'] + " was added to the MongoDB", mimetype='application/json', status=200)
    else:
        return Response("This action requires admin rights", mimetype='application/json', status=400)

@app.route('/delete_product', methods=['GET'])
def delete_product():
    # Διαγραφή προϊόντος
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not has_required_fields(("id",), data):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'], "Admin"):
        if products.find_one({"_id" : ObjectId(data["id"])}) is None:
            return Response("There isn't any product with this id", mimetype='application/json', status=400)
        else:
            products.find_one_and_delete({"_id" : ObjectId(data["id"])})
            return Response("Successful product deletion", mimetype='application/json', status=200)
    else:
        return Response("This action requires admin rights", mimetype='application/json', status=400)

@app.route('/update_product', methods=['GET'])
def update_product():
    # Ενημέρωση προϊόντος
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500, mimetype='application/json')
    if data is None:
        return Response("bad request", status=500, mimetype='application/json')
    if not ("id" in data) or (not ("name" in data) and not ("price" in data) and not ("description" in data) and not ("stock" in data)):
        return Response("Information incomplete", status=500, mimetype="application/json")

    if is_session_valid(request.headers['authorization'], "Simple"):
        if products.find_one({"_id": ObjectId(data["id"])}) is None:
            return Response("There isn't any product with this id", mimetype='application/json', status=400)
        else:
            for field in ("name","description","stock"):
                try:
                    products.find_one_and_update({"_id": ObjectId(data["id"])},{"$set":{field:data[field]}})
                except KeyError:
                    pass
            try:
                products.find_one_and_update({"_id": ObjectId(data["id"])}, {"$set": {"price": float(data["price"])}})
            except KeyError:
                pass
            return Response("Successful product update", mimetype='application/json', status=200)
    else:
        return Response("This action requires admin rights", mimetype='application/json', status=400)

"""
@app.route('/test/<int:where>')
def test(where):
    import requests
    def get_valid_userUuid():
        return requests.post('http://127.0.0.1:5000/login', data="{\"email\": \"admin@test.gr\", \"password\": \"0\" }").text[10:-21]
    def clear_all():
        global users_sessions
        users.drop()
        products.drop()
        users_sessions = {}
        return Response("Cleared users, products and users_sessions!")

    print("Welcome to test: ",where)

    if where == 1:
        return Response(requests.post('http://127.0.0.1:5000/createUser', data="{\"username\": \"ant\", \"password\": \"0\", \"email\":\"admin@test.gr\" }"))
    elif where == 2:
        return Response(requests.post('http://127.0.0.1:5000/login', data="{\"email\": \"admin@test.gr\", \"password\": \"0\" }"))
    elif where == 3:
        return Response(requests.get('http://127.0.0.1:5000/addTo_cart',
                                     data="{\"id\":\"60c9bc0d42de83be95881632\",\"quantity\":3}",
                      headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 4:
        return Response(requests.get('http://127.0.0.1:5000/show_cart', headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 5:
         return Response(requests.get('http://127.0.0.1:5000/deleteItem_cart', data="{\"id\":\"60c9bc0d42de83be95881632\"}", headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 6:
         return Response(requests.get('http://127.0.0.1:5000/buyProducts_cart', data="{\"card_number\":\"1234567891234500\"}", headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 7:
         return Response(requests.get('http://127.0.0.1:5000/show_history', headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 8:
         return Response(requests.get('http://127.0.0.1:5000/delete_user', headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 9:
         return Response(requests.get('http://127.0.0.1:5000/delete_product', data="{\"id\":\"60c9bc0d42de83be95881632\"}", headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 10:
         return Response(requests.get('http://127.0.0.1:5000/update_product', data="{\"id\":\"60c9bc7472c411f964fc8871\",\"name\":\"poniros\",\"price\":500,\"description\":\"o giorgos einai poniros\", \"stock\":0}", headers=json.loads("{\"authorization\":\"" + get_valid_userUuid() + "\"}")))
    elif where == 2873:
        return clear_all()

    return Response("Emmm ok..?")
"""

if __name__ == '__main__':
    # Εκτέλεση flask service σε debug mode, στην port 5000.
    app.run(debug=True, host='0.0.0.0', port=5000)
