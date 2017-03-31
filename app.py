#!/usr/bin/env python
import os
from sets import ImmutableSet
from flask import Flask, abort, request, jsonify
import requests
from werkzeug.contrib.fixers import ProxyFix

IP_WHITELIST = ImmutableSet()
if 'IP_WHITELIST' in os.environ:
    IP_WHITELIST = ImmutableSet(os.environ['IP_WHITELIST'].split(','))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.before_request
def limit_remote_addr():
    if len(IP_WHITELIST) > 0 and request.remote_addr not in IP_WHITELIST:
        abort(403)

@app.route('/')
def index():
    return 'Infrastructure Coding Exercise'

def get_contributors(owner, repo):
    remote_url = "https://api.github.com/repos/{owner}/{repo}/stats/contributors".format(owner=owner, repo=repo)
    return requests.get(remote_url, headers={'Accept': 'application/vnd.github.v3+json'}).json()

def parse_contributor(json_data, contributor): 
    data = {}
    for _, contributor_stats in enumerate(json_data):
        author = contributor_stats['author']['login']
        if author == contributor:
            data[contributor] = {'commits':0, 'additions':0, 'deletions':0}

            for _, week in enumerate(contributor_stats['weeks']):
                data[author]['commits'] = data[author]['commits'] + week['c']
                data[author]['additions'] = data[author]['additions'] + week['a']
                data[author]['deletions'] = data[author]['deletions'] + week['d']
            
            return data
    
    return data

@app.route('/api/stats/<owner>/<repo>/<contributor>')
def repoStats(owner, repo, contributor):
    contributor_stats = parse_contributor(get_contributors(owner, repo), contributor)

    if contributor not in contributor_stats:
        abort(404)
    
    total = contributor_stats[contributor]['additions'] + contributor_stats[contributor]['deletions']
    average = float(total) / float(contributor_stats[contributor]['commits'])
    return jsonify({ 'contributor': contributor, 'average':average})

if __name__ == "__main__":
    app.run()