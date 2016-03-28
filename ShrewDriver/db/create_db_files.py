"""
Opens ShrewDriver 1 event logs / settings files.

Produces  output for use with the UI graphs.
"""
from __future__ import division

import os
import traceback

from db_history import *
from db_performance import *
from db_events import *
from db_lick_times import *

import sys
sys.path.append("..")

from analysis.discrimination_analysis import DiscriminationAnalysis

def get_session_dirs():
    """Returns results dir of every session for every shrew."""

    all_sessionDirs = []
    shrewDirs = filter(os.path.isdir, [DATA_DIR + os.sep + f for f in os.listdir(DATA_DIR)])
    for shrewDir in shrewDirs:
        dateDirs = filter(os.path.isdir, [shrewDir + os.sep + f for f in os.listdir(shrewDir)])
        for dateDir in dateDirs:
            sessionDirs = filter(os.path.isdir, [dateDir + os.sep + f for f in os.listdir(dateDir)])
            all_sessionDirs.extend(sessionDirs)
    return all_sessionDirs


def get_log_and_settings_files(sessionDir):
    logFile = None
    settingsFile = None
    for f in os.listdir(sessionDir):
        filepath = sessionDir+os.sep+f
        if os.path.isfile(filepath) and filepath.endswith("settings.txt"):
            settingsFile = filepath
        if os.path.isfile(filepath) and filepath.endswith("log.txt"):
            logFile = filepath
    return (logFile, settingsFile)


def get_sessions_for_shrew(shrewName):
    """If db files exist, find out what sessions they have.
    Used for populating dropdown in UI."""
    infile = DATA_DIR + os.sep + shrewName.capitalize() + os.sep + shrewName.capitalize() + "_performance.db"
    shelf = shelve.open(infile)
    sessions = shelf.keys()
    shelf.close()
    return sorted(sessions)

if __name__ == "__main__":
    """
    Trawl through all shrew data files
    Produce output files usable by UI graphs
    """

    #analyze all data
    sessionDirs = get_session_dirs()
    analyses = []
    for s in sessionDirs:
        try:
            (logFile, settingsFile) = get_log_and_settings_files(s)
            if logFile is not None and settingsFile is not None:
                print "analyzing", (logFile, settingsFile)
                a = DiscriminationAnalysis(logFile, settingsFile, None)
                if len(a.trials) < 30:
                    continue
                a.trial_stats()
                analyses.append(a)
        except Exception as e:
            print "Can't process file ", logFile
            print traceback.print_exc()

    # make database files
    shrewNames = list(set(a.shrewName for a in analyses))
    for name in shrewNames:
        shrewAnalyses = []
        for a in analyses: # type: DiscriminationAnalysis
            if a.shrewName == name:
                shrewAnalyses.append(a)

        print "Making dbs for", name
        DbHistory().make(shrewAnalyses)
        DbPerformance().make(shrewAnalyses)
        DbLickTimes().make(shrewAnalyses)
        DbEvents().make(shrewAnalyses)
