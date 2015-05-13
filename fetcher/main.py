from constants import REPO_BASE_DIR
import rethinkdb as r
import sys
from fetcher import Cloner
from git import Repo
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from subprocess import Popen


def setup_database():
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    try:
        r.db_create(RDB_NAME).run(connection)
        r.db(RDB_NAME).table_create('developers').run(connection)
        r.db(RDB_NAME).table_create('projects').run(connection)
        r.db(RDB_NAME).table_create('projectdevelopers').run(connection)
        print("Database setup completed. Rerun without --setup.")
    except RqlRuntimeError:
        print("Runtime error. Database might already exist. Try running without --setup.")
    finally:
        connection.close()


def git_stats(cwd):
    repo = Repo(cwd)
    d = {}
    for commit in repo.iter_commits('master'):
        if commit.author.email in d:
            d[commit.author.email]["commits"] += 1
        else:
            d[commit.author.email] = {"author": commit.author.name,
                                      "commits": 1}
    return d


def submit_stats(url, code):
    tmp = url.split('/')[-2:]
    gitdir = REPO_BASE_DIR + '/' + tmp[0] + '/' + tmp[1]
    print(gitdir)
    
    print(git_stats(gitdir))

if __name__ == '__main__':
    if "--setup" in sys.argv:
        setup_database()
    else:
        REPOCLONER = Cloner(submit_stats)
        REPOCLONER.add_work("https://github.com/johnwalker/lein-plz")
        REPOCLONER.add_work("https://github.com/johnwalker/astrolander")
        while True:
            pass
    
