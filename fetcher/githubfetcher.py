from subprocess import Popen
from queue import Queue
from threading import Thread, Lock
import os

REPO_BASE_DIR = "/home/john/repositories"

def make_reposubdir(repo):
    return REPO_BASE_DIR + "/"+ repo.split('/')[0]

def git_clone(url, cwd):
    return Popen(["git", "clone", url], cwd=cwd)

def gh_clone(repo):
    '''Example usage: gh_clone("technomancy/leiningen").wait()
    
    Creates the directory REPO_BASE_DIR + technomancy.

    Returns a process that clones leiningen into REPO_BASE_DIR +
    technomancy + leiningen. Use .wait() to wait for the process to
    finish.
    '''
    reposubdir = make_reposubdir(repo)
    if not os.path.exists(reposubdir):
        os.makedirs(reposubdir)
    return git_clone("https://github.com/" + repo, cwd = reposubdir)

class Cloner:
    # 
    def __init__(self, handler):
        '''handlers are functions that accept two arguments, repo and code.
        '''
        self.q = Queue()
        self.f = handler
        self.worker = Thread(target=self._work)
        self.worker.setDaemon(True)
        self.worker.start()
    
    def add_work(self, repo):
        '''Add a repository to be cloned'''
        self.q.put(repo)
        
    def _work(self):
        while True:
            if not self.q.empty():
                next_url = self.q.get()
                code = gh_clone(next_url).wait()
                self.q.task_done()
                self.f(next_url, code)
                
if __name__ == '__main__':
    def my_notifier(repo, code):
        print("Finished cloning repo " + repo + " with code " + str(code))
    x = Cloner(my_notifier)
    x.add_work("johnwalker/lein-plz")
    x.add_work("johnwalker/astrolander")
    while True:
        pass
