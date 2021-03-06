import os
import pymongo
import json
if os.path.exists("env.py"):
    import env
MONGO_URI = os.environ.get("MONGO_URI")
DATABASE = "ms3_quotes"
COLLECTION_QUTOES = "quotes"
COLLECTION_AUTHORS = "authors"
COLLECTION_BOOKS = "books"


def mongo_connect(url):
    try:
        conn = pymongo.MongoClient(url)
        print("Mongo is connected")
        return conn
    except pymongo.errors.ConnectionFailure as e:
        print("Could not connect to MongoDB: %s") % e


conn = mongo_connect(MONGO_URI)
coll1 = conn[DATABASE][COLLECTION_QUTOES]
coll2 = conn[DATABASE][COLLECTION_AUTHORS]
coll3 = conn[DATABASE][COLLECTION_BOOKS]

documents_authors = coll1.find(
    {}, {"_id": 0, "Author": 1})
documents = coll1.find()
documents2 = coll2.find()
documents3 = coll3.find()

# All code has been run to clean database and does not need to be ran again

# Check for dupe quotes
store_quotes = []
for doc in documents:
    if doc["Quote"] in store_quotes:
        print(doc["Quote"])
    store_quotes.append(doc["Quote"])

# Update quote image if author has image
image_authors = []
for doc in documents2:
    try:
        if doc["image"]:
            image_authors.append(doc["Author"])
    except:
        pass
for doc in documents:
    if doc["Author"] in image_authors:
        image = coll2.find_one({"Author":  doc["Author"]})["image"]
        coll1.update_many(
            {"Author": doc["Author"]},
            {"$set": {"image": image}})

# Identify most Frequently used tags for mood board
tags = []
frequent = []
for doc in documents:
    list = doc["Tags"]
    for item in list:
        tags.append(item)
for x in tags:
    if tags.count(x) > 500 and x not in frequent:
        frequent.append(x)
print(frequent)


# Remove empty array elements for books
for doc in documents2:
    list1 = doc["Books"]
    for item in list1:
        if item == "":
            coll2.update_one({"Author": doc["Author"]}, {
                             "$pull": {"Books": ""}})
        if item == []:
            coll2.update_one({"Author": doc["Author"]}, {
                             "$pull": {"Books": []}})

# Remove empty array elements for categories
for doc in documents2:
    list1 = doc["Categories"]
    for item in list1:
        if item == "":
            coll2.update_one({"Author": doc["Author"]}, {
                             "$pull": {"Categories": ""}})
        if item == []:
            coll2.update_one({"Author": doc["Author"]}, {
                             "$pull": {"Categories": []}})

# write all books & authors & Categories to author db
store_authors = []
for doc in documents:
    if doc["Author"] not in store_authors:
        store_authors.append(doc["Author"])
        coll2.insert_one({"Author": doc["Author"]})
        try:
            coll2.update_one(
                {"Author": doc["Author"]},
                {"$addToSet": {"Books": doc["Book"]}})
            coll2.update_one(
                {"Author": doc["Author"]},
                {"$addToSet": {"Categories": doc["Category"]}})
        except:
            coll2.update_one({"Author": doc["Author"]},
                             {"$addToSet": {"Books": []}})
            coll2.update_one({"Author": doc["Author"]},
                             {"$addToSet": {"Categories": []}})
    else:
        try:
            coll2.update_one({"Author": doc["Author"]},
                             {"$addToSet": {"Books": doc["Book"]}})
            coll2.update_one({"Author": doc["Author"]},
                             {"$addToSet": {"Categories": doc["Category"]}})
        except:
            coll2.update_one({"Author": doc["Author"]},
                             {"$addToSet": {"Books": []}})
            coll2.update_one({"Author": doc["Author"]},
                             {"$addToSet": {"Categories": []}})


# write all books & authors & Categories to books db --
store_books = []
for doc in documents:
    try:
        if doc["Book"] != "":
            if doc["Book"] not in store_books:
                store_books.append(doc["Book"])
                # print(doc["Author"])
                coll3.insert_one(
                    {"Book": doc["Book"], "Author": doc["Author"]})
                coll3.update_one({"Book": doc["Book"]}, {
                                 "$addToSet": {"Categories": doc["Category"]}})
            else:
                coll3.update_one({"Book": doc["Book"]}, {
                                 "$addToSet": {"Categories": doc["Category"]}})
    except:
        pass

# Remove empty array elements for book categories
for doc in documents3:
    list1 = doc["Categories"]
    for item in list1:
        if item == "":
            coll3.update_one(
                {"Book": doc["Book"]}, {"$pull": {"Categories": ""}})
        if item == []:
            coll3.update_one(
                {"Book": doc["Book"]}, {"$pull": {"Categories": []}})
        if item == "books":
            coll3.update_one(
                {"Book": doc["Book"]}, {"$pull": {"Categories": "books"}})


# Split and update the Author and Books fields
for doc in documents_authors:
    k = doc["Author"].split(",")
    try:
        coll1.update_one({"Author": doc["Author"]}, {"$set": {"Book": k[1]}})
        coll1.update_one({"Author": doc["Author"]}, {"$set": {"Author": k[0]}})
    except:
        pass


# Add book key to collection
with open('data.txt') as json_file:
    data = json.load(json_file)
    store_list = []
    for p in data:
        p['Book'] = ''
        store_list.append(p)
with open('data_copy.txt', 'w') as filehandle:
    json.dump(store_list, filehandle)


# Insert data.txt json content to collection
with open('data.txt') as json_file:
    data = json.load(json_file)
    for p in data:
        coll1.insert_one(p)

# Remove Duplicated quotes
coll.ensureIndex({"Quote": 1}, {unique: true, dropDups: true})
