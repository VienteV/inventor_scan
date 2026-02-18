import json
import sqlite3

import sql_operations as db

with open("assembly_components.json", 'r') as file:
    try:
        assembly = json.load(file)
    except Exception as e:
        print(e)

def get_amount(name):
    amount = name.split(":")[1]
    return amount


for i in assembly:
    if "КЛГИ" in i["partNumber"]:
        try:
            db.insert_into_details(i["partNumber"], i["Description"], 1, i["parent"])
        except Exception as e:
            print(e, i)
