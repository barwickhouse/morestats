from constants import REPO_BASE_DIR, RDB_HOST, RDB_PORT, RDB_NAME
import rethinkdb as r
import sys
from fetcher import Cloner
from git import Repo
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from subprocess import Popen


def setup_database():
    try:
        r.db_create(RDB_NAME).run(connection)
        r.db(RDB_NAME).table_create('project', primary_key='path').run(connection)
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

    contributors = []
    for k, v in d.items():
        contributors.append(v)
        contributors[-1]["email"] = k

    return contributors


def submit_stats(url, code):
    path = url.split('/')[-2:]
    gitdir = REPO_BASE_DIR + '/' + path[0] + '/' + path[1]
    contributors = git_stats(gitdir)
    project = {"path": path,
               "contributors": contributors}
    r.db(RDB_NAME).table("project").insert(project).run(connection)

if __name__ == '__main__':
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    print(r.db(RDB_NAME).table("project").run(connection))
    if "--setup" in sys.argv:
        setup_database()
    else:
        REPOCLONER = Cloner(submit_stats)
        REPOCLONER.add_work("https://github.com/johnwalker/lein-plz")
        REPOCLONER.add_work("https://github.com/johnwalker/astrolander")
        while True:
            pass
    
