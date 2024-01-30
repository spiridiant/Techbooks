import socket
import threading
import pymongo
import json
from bson.json_util import dumps, loads

HEADER = 64

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((socket.gethostname(), 5051))

#add books into cart --By Donghwan, Taebin
def addbook(client):
    while True:
        msg = receive(client)
        if msg:
            print(msg)
            if "Book added" in msg:
                break

        id = input("   Input: ")
        send(id, client)  

#remove books from cart for user --By Taebin        
def removebook(client):
    while True:
        msg = receive(client)
        if msg:
            print(msg)
            if "Book removed" in msg:
                break
            elif "dont have" in msg:
                break

        id = input("   Input: ")
        send(id, client)      

#checkout for user --By Donghwan
def checkout(client):
    while True:
        msg = receive(client)
        if msg:
            print(msg)
        
        option = input("\n*********Do you want to finalize your order?*********\n     Please Enter 1 for Yes or 2 for No: ")
        send(option, client)
        
        if option == "1":
            print("\n---------Thank you for shopping with us!!!!---------\n")
            break
        elif option == "2":
            break

#shopping cart for user --By Donghwan
def shoppingCart(client):
    while True:
        msg = receive(client)
        count = 0;
        if msg:
            print(msg)
            count = showBook(client)
        option = input(f'\n***You have {count}  books***\n\n   1)Remove books\n   2)Checkout\n   3)Go back to the previous option\n   Enter 1-3: ')
        send(option, client)
        
        if option == "1":
            removebook(client)
        elif option == "2":
            checkout(client)
        elif option == "3":
            break


#bookpage for user --By Donghwan
def bookPage(client):
    while True:
        msg = receive(client)
        if msg:
            print(msg)
            if("END" in msg):
                msg = receive(client)
                print(msg)

        option = input("\n   Enter 0-4: ")
        send(option, client)

        if option == "0":
            addbook(client)
        elif option == "1" or option == "2" or option == "3":
            showBook(client)
        elif option == "4":
            break

#read a json file that contains a list of books from the server and display the books -By Donghwan, Eli
def showBook(client):
    data = client.recv(2048).decode()
    bookList = json.loads(data)
    count = 0;
    if(len(bookList) > 0):
        print(f'\n{"ID":<10s}{"Title":<70s}{"Author":<25s}{"Price":<15s}{"Course":<15s}{"Tag":<15s}')
        for book in bookList:
            count += 1
            x = book["tags"][0]
            print(f'\n{book["_id"]:<10s}{book["title"]:<70s}{book["author"]:<25s}{book["price"]:<15s}{book["course"]:<15s}{x:<15s}')
    return count
        
#registrate the user. --By Eli
def registration(client):
    while True:
        msg = receive(client)
        if msg:
            print(msg)
            if("Your account has been created" in msg): 
                break
        userin = input("")
        send(userin, client)
    login(client)

#Login the user --By Eli
def login(client):
    while True:
        msg = receive(client)
        if msg:
            print(msg)
            if("Welcome!" in msg):
                break
        userin = input("")
        send(userin, client)
    homepage(client)

#allows the user to view and change their account info --By Eli
def accoutInfo(client):
    while True:
        print("This is your account info: ")
        data = client.recv(1024).decode() # receive a json file
        dataJson = json.loads(data)     #load the json file to a object

        username = dataJson.get("username")
        fname = dataJson.get("fname")
        lname = dataJson.get("lname")
        email = dataJson.get("email")
        userin = input(f"Username: {username}\nFirst Name: {fname}\nLast Name: {lname}\nEmail: {email}\n\nEnter 1 to change your first name\nEnter 2 to change your last name\nEnter 3 to change your email\nEnter 4 to change your password\nEnter 5 to go back to the homepage\n")
        send(userin, client)
        if userin == "1":
            newFname = input("Please enter your new first name: ").capitalize()
            send(newFname, client)
        elif userin == "2":
            newLname = input("Please enter your new last name: ").capitalize()
            send(newLname, client)
        elif userin == "3":
            newEmail = input("Please enter your new email: ")
            send(newEmail, client)
            valid = receive(client)
            while valid != "good":
                newEmail = input(valid)
                send(newEmail, client)
                valid = receive(client)
        elif userin == "4":
            newPwd1 = input("Please enter your new password: ")
            send(newPwd1, client)
            newPwd2 = input("Please confirm your password: ")
            send(newPwd2, client)
            valid = receive(client)
            while valid != "good":
                newPwd2 = input(valid)
                send(newPwd2, client)
                valid = receive(client)
            print("Your password has been updated.")
        elif userin == "5":
            break
        else:
            print("Invalid option")
        print("\n**Your Info has been updated**\n")

#order history --By Taebin        
def pastOrders(client):
    print("\n***ORDER HISTORY***")
    hist = receive(client)
    while hist != "End":
        print(hist)
        hist = receive(client)


#the homepage menu --By Eli
def homepage(client):
     while True:
        msg = receive(client)
        if msg:
            print(msg)
        option = input("\n   Enter 1-5: ")
        send(option, client)
        if option == "1":
            bookPage(client)
        elif option == "2":
            shoppingCart(client)
        elif option == "3":
            accoutInfo(client)
        elif option == "4":
            pastOrders(client)
        elif option == "5":
            break

#send message. msg is the message string you want to send, clientsocket is the socket --By Eli
def send(msg, client):
    msg = f'{len(msg):<{HEADER}}' + msg
    client.send(bytes(msg, "utf-8"))
    
#receive a string from the socket --By Eli
def receive(client):
    msg_len = client.recv(HEADER).decode("utf-8")
    if msg_len:
        msg_len = int(msg_len)
        msg = client.recv(msg_len).decode("utf-8")
        return msg
    else: return None

#the start menu --By Eli
def main():
    while True:
        msg = receive(client)
        if msg:
            print(msg)
          
        option = input("\n   Enter 1-3: ")
        send(option, client)
        if option == "1":
            login(client)
        elif option == "2":
            registration(client)
        elif option == "3":
            break
    client.close()
        
if __name__ == "__main__":
    main()