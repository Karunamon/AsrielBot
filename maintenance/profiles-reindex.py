import json
import blitzdb
import configparser
import os
import sys
from blitzdb import Document, FileBackend

#INSTRUCTIONS
#1. Run from Asrielbot's main folder
#2. Run as the user Asrielbot usually runs as
#3. Move existing DB folders into a temp location
#4. Point this script at the _db folder's objects directory. For memos, this is memos_db/memo/objects/ - include the trailing /
#5, Run.
#6. ???
#7. Profit

ini = configparser.ConfigParser()
ini.read('config.ini')


class Profile(Document):
    pass

db = FileBackend(ini.get('Profiles', 'main_db'))

files = [x for x in os.listdir(sys.argv[1])]

print("Got %s objects to reinsert." % len(files))
input("Enter to continue.")

for filename in files:
    with open(sys.argv[1] + filename,'r') as handle:
        j = json.load(handle)
        print("Profile belonging to %s..." % j['owner'], end=" ")
        del(j['pk'])   # Throw out the bogus primary key
        newmemo = Profile(j)
        newmemo.save(db)
        db.commit()
        print("committed.")
        
