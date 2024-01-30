import socket
import threading
import pymongo
import json
import re
from bson.json_util import dumps, loads
from Functions import *
from datetime import datetime


regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

dbconnection = pymongo.MongoClient("mongodb+srv://techbooks:1234@cluster0.mavgqyg.mongodb.net")
db = dbconnection["MyDB"]
dbBooks = db["books"]
dbUsers = db["users"]
dbOrders = db["orders"]
dbHistory = db["history"]

HEADER = 64
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((socket.gethostname(), 5051))


#Checkout --By Donghwan, Taebin
def checkout(username, clientsocket):
    while True:
        printOrderSummary(username, clientsocket)
        option = receive(clientsocket)
        if(option == "1"):
            date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            user = dbOrders.find_one({"username":username})
            if user["cartItem"]:
                user["_id"] = len(list(dbHistory.find({}))) + 1
                user["purchaseDate"] = date
                dbHistory.insert_one(user)
                 
            dbOrders.find_one_and_update({"username":username},{"$set":{"cartItem":[]}})
            break
        elif(option == "2"):
            break
    # CHECKOUT FORMAT
    # total items: 12 int
    # items price: $00.00 float 
    # Discount savings: $0.00 float
    # total before tax = $00.00 float
    # estimated tax: $00.00 float
    # ---------------------------
    # Order Total: $00.00 float
    
    # price after tax
    # pay - if pay, send cartItem into history

#shopping cart for users to put books in or out --by Donghwan
def shoppingCart(username, clientsocket):
    
    while True:
        send("\n***Shopping Cart***", clientsocket)
        showShoppingCart(username, clientsocket)
        option = receive(clientsocket)
        if option == "1":
            removeBook(username, clientsocket)
        elif option == "2":
            checkout(username, clientsocket)
        elif option == "3":
            break

#bookpage where users can browse books --By Donghwan
def bookPage(username, clientsocket):
    
    while True:
        send("\n***Bookpage***\n\n**Holiday Sales is here!! Shop for $150 to get a 15% discount on the whole order!!**\n\nPlease select an option,\n\n   0)Add books\n   1)Show books alphabetically by titles\n   2)Show books numberically by price\n   3)Show books by the related courses\n   4)Go back to the previous option", clientsocket)
        option = receive(clientsocket)
        if option == "0":
            addBook(username, clientsocket)
        elif option == "1":
            sortingAlphabet(clientsocket)
        elif option == "2":
            sortingNum(clientsocket)
        elif option == "3":
            sortingCourse(clientsocket)
        elif option == "4":
            break

#allows the user to view and change their account info --By Eli
def accoutInfo(username, clientsocket):
    while True:
        #transfer a cursor to json file and send it to client
        userInfo = json.dumps(dbUsers.find_one({"username": username}), default=str)  
        clientsocket.send(userInfo.encode())
        
        userin = receive(clientsocket)
        if userin == "1":
            fname = receive(clientsocket)
            dbUsers.update_one({"username": username}, {"$set": {"fname": fname}})
        elif userin == "2":
            lname = receive(clientsocket)
            dbUsers.update_one({"username": username}, {"$set": {"lname": lname}})
        elif userin == "3":
            email = receive(clientsocket)
            while not validEmail(email) or dbUsers.find_one({"email": email}):
                if not validEmail(email):
                    send("\nInvalid email address, please try again:", clientsocket)
                else:
                    send("\nEmail address already exisits, please try again:", clientsocket)
                email = receive(clientsocket)
            send("good", clientsocket)
            dbUsers.update_one({"username": username}, {"$set": {"email": email}})
        elif userin == "4":
            passwd1 = receive(clientsocket)
            passwd2 = receive(clientsocket)
            while passwd2 != passwd1:
                send("\nThe passwords are not the same, please try again: ", clientsocket)
                passwd2 = receive(clientsocket)
            send("good", clientsocket)
            dbUsers.update_one({"username": username}, {"$set": {"password": passwd1}})
        elif userin == "5":
            break
        

#keep order histroy --By Taebin
def pastOrders(username, clientsocket):
    if dbHistory.find({'username': username}):
        for eachOrder in dbHistory.find({'username': username}):
            hist = "*Purchase Date*: " + eachOrder["purchaseDate"] + "\n"
            hist += f'\n{"ID":<10s}{"Title":<70s}{"Author":<25s}{"Price":<15s}{"Course":<15s}{"Tag":<15s}'
            for bookID in eachOrder["cartItem"]:
                book = dbBooks.find_one({"_id":bookID})
                hist += '\n{:<10s}{:<70s}{:<25s}{:<15s}{:<15s}{:<15s}'.format(book["_id"], book["title"], book["author"], book["price"], book["course"], book["tags"][0])
            hist += "\n"
            send(hist, clientsocket)
        send("End", clientsocket)
                
    
    # CHECKOUT ADD DATE
    
    
#the homepage menu --By Eli
def homepage(username, clientsocket):
    while True:
        send("\n***Homepage***\nPlease select an option\n\n    1) Browse books\n    2) View shopping cart\n    3) Change Account Info\n    4) View Past Orders\n    5) Log out", clientsocket)
        option = receive(clientsocket)
        if option == "1":
            bookPage(username, clientsocket)
        elif option == "2":
            shoppingCart(username, clientsocket)
        elif option == "3":
            accoutInfo(username, clientsocket)
        elif option == "4":
            pastOrders(username, clientsocket)
        elif option == "5":
            break
            

#registrate the user --By Eli
def registration(clientsocket):
    
    send("\nPlease choose a username. Please note the uername is UNIQUE to each user and CAN NOT be changed:", clientsocket)
    username = receive(clientsocket)
    while dbUsers.find_one({"username": username}):
        send("\nUsername already exisits, please enter a different name:", clientsocket)
        username = receive(clientsocket)
        
    send("\nPlease enter your email:", clientsocket)
    email = receive(clientsocket)
    while not validEmail(email) or dbUsers.find_one({"email": email}):
        if not validEmail(email):
            send("\nInvalid email address, please try again:", clientsocket)
        else:
            send("\nEmail address already exisits, please try again:", clientsocket)
        email = receive(clientsocket)
            
    send("\nPlease choose your password:", clientsocket)
    passwd1 = receive(clientsocket)
    send("\nPlease comfirm your password:", clientsocket)
    passwd2 = receive(clientsocket)
    while passwd2 != passwd1:
        send("\nThe passwords are not the same, please try again:", clientsocket)
        passwd2 = receive(clientsocket)
        
    send("\nPlease enter your first name:", clientsocket)
    fname = receive(clientsocket).capitalize()
    send("\nPlease enter your last name:", clientsocket)
    lname = receive(clientsocket).capitalize()
    
    newUser = {"username": username, "email": email, "password": passwd1, "fname": fname, "lname": lname}
    dbUsers.insert_one(newUser)
    send("\n**Your account has been created, " + fname + ".***\n**********Now please login**********", clientsocket)
    #Add user to the user database to prevent error --By Donghwan
    if not dbOrders.find_one({"username":username}):
        dbOrders.insert_one({"username": username, "cartItem": []})
    login(clientsocket)

#Login the user --By Eli
def login(clientsocket):
    send("\nPlease Enter Your Username:", clientsocket)
    username = receive(clientsocket)
    while not dbUsers.find_one({"username": username}):
        send("\nInvalid Username, please try again:", clientsocket)
        username = receive(clientsocket)
    send("\nPlease Enter Your Password:", clientsocket)
    passwd = receive(clientsocket)

    while not dbUsers.find_one({"username": username, "password": passwd}):
        send("\nInvalid password, please try again:", clientsocket)
        passwd = receive(clientsocket)
    send("\n\n***Welcome! " + username + "!***", clientsocket)
    #By -- Donghwan
    if not dbOrders.find_one({"username":username}):
        dbOrders.insert_one({"username": username, "cartItem": []})
    homepage(username, clientsocket)

#connect with a client and handle it. --By Eli
def handle(clientsocket, address):
    print(f"Connection from {address} has been established! \n")
    
    connected = True
    while connected:
        send("\n*********Welcome To The Techbooks!********* \n\nPlease Follow The Menu For Next Step \n    1) Login \n    2) Sign up \n    3) Disconnect", clientsocket)
        msg = receive(clientsocket)
        if msg:
            if(msg == "1"):
                login(clientsocket)
            elif(msg == "2"):
                registration(clientsocket)
            elif(msg == "3"):
                connected = False
            else: send("\nInvalid Option", clientsocket)
    clientsocket.close()

#start a connection with a client, handle it in a thread --By Eli
def start():
    while True:
        server.listen() 
        clientsocket, address = server.accept()
        thread = threading.Thread(target=handle, args=(clientsocket, address))
        thread.start()
        if KeyboardInterrupt:
            exit()
            
if __name__ == "__main__":
    print("Server started.")
    start()