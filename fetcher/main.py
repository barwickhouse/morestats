from constants import REPO_BASE_DIR, RDB_HOST, RDB_PORT, RDB_NAME
import rethinkdb as r
import sys
from fetcher import Cloner
from git import Repo
from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from subprocess import Popen
import requests, json

def get_genders(names):
    url = ""
    cnt = 0
    for name in names:
        if url == "":
            url = "name[0]=" + name
        else:
            cnt += 1
            url = url + "&name[" + str(cnt) + "]=" + name
    req = requests.get("http://api.genderize.io?" + url)
    results = json.loads(req.text)
    retrn = []
    for result in results:
        print(result)
        if "gender" in result and result["gender"]:
            retrn.append((result["gender"], result["probability"], result["count"]))
        else:
            retrn.append(('None','0.0',0.0))
    return retrn

def setup_database():
    try:
        r.db_create(RDB_NAME).run(connection)
        r.db(RDB_NAME).table_create('sex', primary_key='name').run(connection)
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
    contributor_genders(contributors)

def partition(lst, n):
    lsts = []
    tmp = []
    for e in lst:
        tmp.append(e)
        if len(tmp) == n:
            lsts.append(tmp)
            tmp = []
    else:
        if tmp:
            lsts.append(tmp)
    return lsts

def contributor_genders(contributors):
    names = []
    genders = []
    base = 0
    for contributor in contributors:
        # gotta get first name
        authorname = contributor["author"].split(' ')
        if authorname and authorname[0].isalpha():
            names.append(authorname[0])

    unentered_names = []
    for name in names:
        x = r.db(RDB_NAME).table('sex').get(name).run(connection)
        if not x:
            unentered_names.append(name)
            
    questions = partition(unentered_names, 10)
    i = 0
    for question in questions:
        answers = get_genders(question)
        for answer in answers:
            r.db(RDB_NAME).table("sex").insert({"name": unentered_names[i],
                                                "sex": answer[0],
                                                "probability": answer[1]}).run(connection)
    tuples = []
    c = 0
    for contributor in contributors:
        tuples.append((contributor["author"], r.db(RDB_NAME).table("sex").get(names[c]).run(connection)))
        c += 1
    print (tuples)
    return tuples
    
    
if __name__ == '__main__':
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    if "--setup" in sys.argv:
        setup_database()
    else:
        REPOCLONER = Cloner(submit_stats)
        REPOCLONER.add_work("https://github.com/johnwalker/lein-plz")
        REPOCLONER.add_work("https://github.com/johnwalker/astrolander")
        print(r.db(RDB_NAME).table("sex").run(connection))
        print(r.db(RDB_NAME).table("project").run(connection))
        while True:
            pass
    
