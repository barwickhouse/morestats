from git import Repo
import csv
import requests, json
import sys

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
    if req.status_code != 200:
        print("error in get_genders")
        if req.status_code == 429:
            print("genderize.io api request limit reached")
        sys.exit(1)
    results = json.loads(req.text)
    retrn = []
    for result in results:
        if "gender" in result and result["gender"]:
            retrn.append((result["gender"], result["probability"], result["count"]))
        else:
            retrn.append(('None','0.0',0.0))
    return retrn


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

    first_names = set()
    for contributor in contributors:
        authorname = contributor["author"].split(' ')
        # If the first name is exists and is alphabetical
        if authorname and authorname[0].isalpha():
            first_names.add(authorname[0].lower())
            
    first_names = list(first_names)
    name_sex = {}
    # genderize.io lets you submit up to 10 names at a time
    batched_names = partition(first_names, 10)
    for batch in batched_names:
        genderize_results = get_genders(batch)
        for i, result in enumerate(genderize_results):
            name_sex[first_names[i]] = {"sex": result[0],
                                        "probability": result[1]}

    for i, contributor in enumerate(contributors):
        authorname = contributor["author"].split(' ')
        if authorname and authorname[0].isalpha() and authorname[0].lower() in name_sex:
            contributors[i].update(name_sex[authorname[0].lower()])
            
    return contributors


if __name__ == '__main__':
    print(git_stats("/home/john/repositories/johnwalker/lein-plz"))

