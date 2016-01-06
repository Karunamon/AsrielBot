# Simple importer from old database format used by Reibot

from blitzdb import Document, FileBackend

db = FileBackend('profiles_db')


class Profile(Document):
    pass


def importdb():
    print("STARTING PROFILE IMPORT!")
    f = open('profiles.txt', 'r')
    for line in f:
        la = line.split("|")
        try:
            profile = db.get(Profile, {'name': la[1].lower()})
        except Profile.DoesNotExist:
            profile = Profile(
                    {
                        'name': la[1].lower(),
                        'owner': la[0].lower(),
                        'lines': [la[3]],
                        'random': False,
                    }
            )
            profile.save(db)
            db.commit()
            print("NEW: %s owned by %s" % (la[1], la[0].lower()))
            continue
        lines_to_append = profile.lines
        lines_to_append.append(la[3])
        profile.save(db)
        db.commit()
        print("UPDATE: Added line to %s" % (la[1]))
        continue


importdb()
print("All done!")
