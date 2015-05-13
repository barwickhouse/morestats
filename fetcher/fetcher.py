'''Functions for cloning from sites like github, gitorous, etc. and
the Cloner class for constructing a single-threaded worker.'''
from constants import REPO_BASE_DIR
import os

from subprocess import Popen
from queue import Queue
from threading import Thread


def repo_to_subdir(url):
    '''Given a url like https://github.com/technomancy/leiningen, return
    REPO_BASE_DIR + technomancy.

    '''
    return REPO_BASE_DIR + "/" + url.split('/')[-2]


def git_clone(url, cwd):
    '''Given a url like https://github.com/stephencolbert/irock and a cwd,
    clone the repo from that cwd.

    '''
    return Popen(["git", "clone", url], cwd=cwd)


def mkdirs_clone(url):
    '''Example usage:

    mkdirs_clone("https://github.com/technomancy/leiningen").wait()

    Creates the directory REPO_BASE_DIR + technomancy.

    Returns a process that clones leiningen into REPO_BASE_DIR +
    technomancy + leiningen. Use .wait() to wait for the process to
    finish.

    '''
    reposubdir = repo_to_subdir(url)
    if not os.path.exists(reposubdir):
        os.makedirs(reposubdir)
    return git_clone(url, cwd=reposubdir)


class Cloner:
    '''A worker with its own queue for cloning repositories located at the
    submitted URLs.

    '''
    def __init__(self, handler):
        '''Build a new cloner. The handler argument should be a function that
        accepts two arguments, repo and code.

        '''
        self.work_queue = Queue()
        self.handler = handler
        self.worker = Thread(target=self._work)
        self.worker.setDaemon(True)
        self.worker.start()
    
    def add_work(self, repo):
        '''Add a repository to be cloned.'''
        self.work_queue.put(repo)
        
    def _work(self):
        '''Loop forever, pulling work off the work_queue to clone github
        repositories and calling the handler upon each finished
        clone.

        '''
        while True:
            if not self.work_queue.empty():
                next_url = self.work_queue.get()
                code = mkdirs_clone(next_url).wait()
                self.work_queue.task_done()
                self.handler(next_url, code)
                
if __name__ == '__main__':
    def my_notifier(repo, code):
        '''An example handler for the cloner.'''
        print("Finished cloning repo " + repo + " with code " + str(code))
    MY_CLONER = Cloner(my_notifier)
    MY_CLONER.add_work("https://github.com/johnwalker/lein-plz")
    MY_CLONER.add_work("https://github.com/johnwalker/astrolander")
    while True:
        pass
