import os
import inspect
import types
import imp

import sys
sys.path.append('..')


class Shrew:

    def __init__(self, py_file_path, name):
        """
        Reads methods inside the python file.
        Each method is a task that the animal can do.
        """

        self.name = name
        self.tasks = []
        self.configs = []

        shrew_module = imp.load_source(name + "_import", py_file_path)

        shrew_module_methods = [shrew_module.__dict__.get(a) for a in dir(shrew_module)
                                if isinstance(shrew_module.__dict__.get(a), types.FunctionType)]
        for m in shrew_module_methods:
            if m.__name__.startswith("_"):
                #Disregard any "private" functions, i.e. ones that start with '_'
                continue
            self.tasks.append(m)

        shrew_module_classes = [shrew_module.__dict__.get(a) for a in dir(shrew_module)
                                if isinstance(shrew_module.__dict__.get(a), types.ClassType)]
        for c in shrew_module_classes:
            if c.__name__ == "Shrew":
                #disregard this class (may be imported).
                continue
            self.configs.append(c)


def get_animals(animalDir):
    """
    Given a dir of shrew Python tasks (i.e. the shrew directory of this project),
    read the names of each shrew and get the tasks they can do.
    This will be used in the UI.
    """
    animals = []

    for f in os.listdir(animalDir):
        animalFilePath = animalDir + os.sep + f
        if os.path.isfile(animalFilePath):
            if f.endswith(".py"):
                name = f.replace(".py", "")
                if name != "shrew" and name != "__init__":
                    animals.append(Shrew(animalFilePath, name))

    return animals

if __name__ == "__main__":
    animals = get_animals(".")
    for a in animals:
        print "\n" + a.name
        for t in a.tasks:
            print t.__name__