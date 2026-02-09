import requests
import json

api_key="8vD5VvhPAxO0BMfmjGEIm8"

DOI1="https://doi.org/10.1016/j.jobe.2024.111150"
DOI2="10.48550/ARXIV.2408.00540"

url1= "https://api.openalex.org/works/"
doi1="https://doi.org/10.1016/j.jobe.2024.111150"
url2= "https://api.openalex.org/works/https://doi.org/10.1186/S42162-021-00153-9"

headers= {"Authorization": f"apikey token=8vD5VvhPAxO0BMfmjGEIm8"}

r1=requests.get(url=url1 + doi1, headers=headers,)
r2=requests.get(url=url2, headers=headers,)

dict=r1.json().keys()

with open("AlexResponse2", "w") as f:
    json.dump(r1.json(), f, indent=4)

print(dict)
    





'''

data= ("title": 
    "display_name": 
    "publication_year": 2021,
    "publication_date": "2021-09-01",
        "type": "article")


with open('authorsTest', 'w') as f:
    json.dump(r2.json()['authorships'], f, indent=4)

I=[]
for i in r2.json()['authorships']:
    a=i["author"]["display_name"]
    I.append(a)

print(I)
#print(r2.json()['authorships'])
'''