import pymongo
import threading
import socket
import json
import re

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
dbconnection = pymongo.MongoClient("mongodb+srv://techbooks:1234@cluster0.mavgqyg.mongodb.net/?retryWrites=true&w=majority")
db = dbconnection["MyDB"]
dbBooks = db["books"]
dbUsers = db["users"]
dbOrders = db["orders"]
dbHistory = db["history"]
HEADER = 64
FORMAT = "utf-8"

#This function checks if entered email is valid upon creation **LOG IN / ACCOUNT CREATION** --By Taebin
def validEmail(email):
    if(re.fullmatch(regex, email)):
        return True
 
    else:
        print("**Please enter a valid email**")
        return False    
        
#Change number format --By Donghwan
def format_num(option):
    if len(option) < 2:
        return "00" + option
    elif len(option) < 3:
        return "0" + option
    return option

#Add Books into shopping cart --By Donghwan and Taebin
def addBook(username, clientsocket):
    send("\nEnter ID number to add the book into your shopping cart: ", clientsocket)

    bookID = receive(clientsocket)
    bookID = format_num(bookID) 

    while not dbBooks.find_one({"_id":bookID}): #Check if the book is available
        send("\nNo book found please enter again", clientsocket)
        bookID = receive(clientsocket)
        bookID = format_num(bookID) 
    
    user = dbOrders.find_one({"username":username})
    if user: #if user has shopping cart already
        user["cartItem"].append(bookID)
        dbOrders.find_one_and_update({"username":username},{"$set":{"cartItem":user["cartItem"]}})
    else: #if no cart made, make one
        x = {"username": username, "cartItem": [bookID]}
        dbOrders.insert_one(x)
    send("\n*Book added*", clientsocket)
    
#Remove Books from shopping cart --By Taebin   
def removeBook(username, clientsocket):
    send("\nEnter ID number to remove the book in your shopping cart: ", clientsocket)

    bookID = receive(clientsocket)
    bookID = format_num(bookID)
    user = dbOrders.find_one({"username":username})
    if user:
        if bookID in user["cartItem"]:
            user["cartItem"].remove(bookID)
            dbOrders.find_one_and_update({"username":username},{"$set":{"cartItem":user["cartItem"]}})
            send("Book removed", clientsocket)
        else:
            send("\nYou dont have the book in your shopping cart", clientsocket)

#Display on the page of shopping cart --by Donghwan and Taebin
def showShoppingCart(username, clientsocket):
    data = []
    userOrder = dbOrders.find_one({"username":username})
    if userOrder["cartItem"]:
        for bookID in userOrder["cartItem"]:
            if list(dbBooks.find({"_id":bookID},{})):
                data = data + list(dbBooks.find({"_id":bookID},{}))
    books = json.dumps(data)
    clientsocket.send(books.encode())

# discounted price (discount() returns a boolean where it is qualified for discount) --By Taebin
def discount(total):
    return int(total) > 150

# return savings amount --By Taebin
def taxAmount(itemPrice):
    return itemPrice * 0.12

# return itemPrice --By Taebin
def discountSavings(itemPrice):
    return itemPrice * 0.15

# sum up prices --By Taebin
def sum(username):
    userOrder = dbOrders.find_one({"username":username})
    total = 0;
    for bookID in userOrder["cartItem"]:
        if dbBooks.find_one({"_id":bookID},{}):
            price = dbBooks.find_one({"_id":bookID})["price"]
            total += float(price)
    return total 
    
    # print("{:10.4f}".format(total))

    
#The number of total items --By Taebin 
def totalItems(username):
    return len(list(dbOrders.find_one({"username":username})["cartItem"])) 

#Summary for Checkout --By Taebin
def printOrderSummary(username, clientsocket):
    totItem = totalItems(username)
    itemPrice = sum(username)

    if discount(itemPrice):
        discSav = discountSavings(itemPrice)
        totBeforeTax = itemPrice - discSav
    else:
        discSav = 0
        totBeforeTax = itemPrice
    
    estTax = taxAmount(totBeforeTax)
    orderTot = totBeforeTax + estTax
    
    line = "\n***CHECKOUT***"
    line += "\ntotal books({})\nitems price:      ${:<10.2f}\nDiscount savings: ${:<10.2f}\ntotal before tax: ${:<10.2f}\nestimated tax:    ${:<10.2f}".format(totItem,itemPrice,discSav,totBeforeTax,estTax)
    line += "\n---------------------------"
    line += "\nOrder Total: $%.2f" % (orderTot)

    send(line, clientsocket)
    
#Sorting books Alphabetically by titles --By Donghwan, Eli
def sortingAlphabet(clientsocket):
    aData = list(dbBooks.find({}).sort("title", 1))
    books = json.dumps(aData)
    clientsocket.send(books.encode())

#Sorting books Numerically by price --By Donghwan,Eli
def sortingNum(clientsocket):
    nData = list(dbBooks.find({}).sort("price", 1))
    books = json.dumps(nData)
    clientsocket.send(books.encode())

#Sorting books by the related courses --By Donghwan,Eli  
def sortingCourse(clientsocket):
    cData = list(dbBooks.find({}).sort("course", 1))
    books = json.dumps(cData)
    clientsocket.send(books.encode())
    
#formats to print --By Donghwan
def display(data, clientsocket):

    n = f'\n{"ID":<10s}{"Title":<70s}{"Author":<25s}{"Price":<15s}{"Course":<15s}{"Tag":<15s}'

    for d in data:
        x = d["tags"][0]
        n += f'\n{d["_id"]:<10s}{d["title"]:<70s}{d["author"]:<25s}{d["price"]:<15s}{d["course"]:<15s}{x:<15s}'
    
    n += "\nEND"
    send (n, clientsocket)

#send message. msg is the message string you want to send, clientsocket is the socket --By Eli
def send(msg, clientsocket):
    msg = f'{len(msg):<{HEADER}}' + msg
    clientsocket.send(bytes(msg, FORMAT))

# #receive a string from the socket --By Eli
def receive(clientsocket):
    msg_len = clientsocket.recv(HEADER).decode(FORMAT)
    if msg_len:
        msg_len = int(msg_len)
        msg = clientsocket.recv(msg_len).decode(FORMAT)
        return msg
