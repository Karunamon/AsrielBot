import json
import blitzdb
import configparser
import os
import sys
from blitzdb import Document, FileBackend

ini = configparser.ConfigParser()
ini.read('config.ini')



class Memo(Document):
    pass

db = FileBackend(ini.get('Memos', 'main_db'))

files = [x for x in os.listdir(sys.argv[1])]

print("Got %s objects to reinsert." % len(files))
input("Enter to continue.")

for filename in files:
    with open(sys.argv[1] + filename,'r') as handle:
        j = json.load(handle)
        print("Memo from %s..." % j['sender'], end=" ")
        del(j['pk'])   # Throw out the bogus primary key
        newmemo = Memo(j)
        newmemo.save(db)
        db.commit()
        print("committed.")
        
