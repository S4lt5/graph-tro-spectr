import requests
import urllib.parse
import argparse
import os
import validators
import json
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()

query_string = "query IntrospectionQuery {\n  __schema {\n    queryType {\n      name\n    }\n    mutationType {\n      name\n    }\n    subscriptionType {\n      name\n    }\n    types {\n      ...FullType\n    }\n    directives {\n      name\n      description\n      locations\n      args {\n        ...InputValue\n      }\n    }\n  }\n}\n\nfragment FullType on __Type {\n  kind\n  name\n  description\n  fields(includeDeprecated: true) {\n    name\n    description\n    args {\n      ...InputValue\n    }\n    type {\n      ...TypeRef\n    }\n    isDeprecated\n    deprecationReason\n  }\n  inputFields {\n    ...InputValue\n  }\n  interfaces {\n    ...TypeRef\n  }\n  enumValues(includeDeprecated: true) {\n    name\n    description\n    isDeprecated\n    deprecationReason\n  }\n  possibleTypes {\n    ...TypeRef\n  }\n}\n\nfragment InputValue on __InputValue {\n  name\n  description\n  type {\n    ...TypeRef\n  }\n  defaultValue\n}\n\nfragment TypeRef on __Type {\n  kind\n  name\n  ofType {\n    kind\n    name\n    ofType {\n      kind\n      name\n      ofType {\n        kind\n        name\n        ofType {\n          kind\n          name\n          ofType {\n            kind\n            name\n            ofType {\n              kind\n              name\n              ofType {\n                kind\n                name\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n}\n"
json_introspection = {"operationName":"IntrospectionQuery","variables":{},"query":query_string}
urlencoded_introspection = urllib.parse.quote(query_string)

json_universal = {"query": "query{__typename}"}
urlencoded_universal = "{__typename}"



def getFullFilePath(targetPath, filename):
    return os.path.join(targetPath, filename)

def checkIsGraphQL(url):
    # Try POST first
    resp = requests.post(url,json=json_universal)
    if resp.status_code == 200:
        if 'application/json' in resp.headers.get('content-type', ''):
            json = resp.json()
            if json:               
                if 'data' in json and '__typename' in json['data']:
                    if json['data']['__typename'] == "Query":            
                        return True
    
    #Otherwise, try a GET
    params = {"query": urlencoded_universal}
    resp = requests.get(url,params=params)
    if resp.status_code == 200:
        if 'application/json' in resp.headers.get('content-type', ''):            
            if json:               
                if 'data' in json and '__typename' in json['data']:
                    if json['data']['__typename'] == "Query":            
                        return True
        
    return False

def performIntrospectionQuery(url):
 # Try POST first
    resp = requests.post(url,json=json_introspection)
    if resp.status_code == 200:
        if 'application/json' in resp.headers.get('content-type', ''):
            json = resp.json()
            if json:                
                if 'data' in json and '__schema' in json['data']:                          
                        return json
    
    #Otherwise, try a GET
    params = {"query": urlencoded_introspection}
    resp = requests.get(url,params=params)
    if resp.status_code == 200:
        if 'application/json' in resp.headers.get('content-type', ''):
            json = resp.json()
            if json:
                print(json)
                if 'data' in json and '__schema' in json['data']:                          
                        return json

    return None


parser = argparse.ArgumentParser(description="Request introspection query from GraphQL URLs")
parser.add_argument("-t", "--targets-file", type=str, help="Targets file one URL per line, to GraphQL endpoints")
parser.add_argument("-u", "--url",  type=str, help="URL to GraphQL endpoint")
parser.add_argument("-o", "--output-path",  type=str, help="Path for output JSON", default=".")
args = parser.parse_args()

if not args.targets_file and not args.url:
    print("Either -u or -t must be supplied")
    exit(1)

if not os.path.exists(args.output_path) or not os.path.isdir(args.output_path):
    print(f"{args.output_path} does not exist!")
    exit(1)
targets = []
if args.url:
    targets = [args.url]
elif args.targets_file:
    with open(args.targets_file,"r") as tf:
        lines = tf.readlines()
        targets = lines

print(f"Checking {len(targets)} targets.")
for t in targets:
    t = t.strip()
    if not validators.url(t):
        print(f"[{Style.BRIGHT}{Fore.RED}-{Style.RESET_ALL}] Cannot query {t} as it is not a valid URL")
        continue

    if not checkIsGraphQL(t):
        print(f"[{Style.BRIGHT}{Fore.RED}-{Style.RESET_ALL}] Cannot query {t} as it does not appear to be a GraphQL instance")
        continue

    print(f"[{Style.BRIGHT}{Fore.YELLOW}*{Style.RESET_ALL}] {t} appears to be a GraphQL Instance!")
    results = performIntrospectionQuery(t)

    
        
    if results:
        print(f"\t[{Style.BRIGHT}{Fore.GREEN}+{Style.RESET_ALL}] Got Schema Results!")
        # Get Hostname from URL for file writing
        hostname = urllib.parse.urlparse(t).netloc
        filename = getFullFilePath(args.output_path,f"{hostname}.json")
        with open(filename,"w") as outfile:            
            json.dump(results,outfile, separators=(',', ': '))            
            print(f"\tSaved to {filename}")
    else:
        print(f"\t[{Style.BRIGHT}{Fore.RED}-{Style.RESET_ALL}] Introspection Failed!")
