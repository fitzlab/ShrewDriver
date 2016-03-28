import os
import shelve

class DbMixin(object):
    """
    Mixin that provides a few common functions to db classes.
    """

    def get(self, animalName):
        if animalName not in self._db:
            dbfile = self.get_path(animalName)
            if not os.path.isfile(dbfile):
                print "Creating db file: " + dbfile
                os.makedirs(os.path.dirname(dbfile))
            with self._lock:
                self._db[animalName] = shelve.open(dbfile, writeback=True, protocol=2)
        return self._db[animalName]

    def sync(self, animalName):
        with self._lock:
            if animalName in self._db:
                self._db[animalName].sync()

    def make(self, analyses):
        """Go through all the provided analysis objects and make / update DB entries."""
        for a in analyses:  # type: sd1_analysis.Analysis
            self.add_entry(a)

    def get_datestr(self, analysis):
        return str(analysis.date.year).zfill(2) + "-" \
            + str(analysis.date.month).zfill(2) + "-" \
            + str(analysis.date.day).zfill(2) + "_" \
            + str(analysis.session).zfill(4)