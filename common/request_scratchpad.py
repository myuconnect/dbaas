import requests

#myHeaders = {"ContentType" : "application/json", "Connection" : "keep-alive"}
myHeaders = {"ContentType" : "application/json"}
myUrl = "http://usdfw21as383v.mrshmc.com:8000/api/cicd/processRequest"
myData = {
    "encKey": "eXokNzl5NEUzOWdXNCkp",
    "userId": "u1167965",
    "method": "getApps4Onboarding",
    "args": {
        "region": "NAM",
        "opco": "MARSH",
        "dbTechnology": "Oracle"
    }
}

myResponse = requests.post(myUrl, headers=myHeaders, data=myParams)
print("url >> ", myResponse.url, "request >>", myResponse.request, "elapsed : ", myResponse.elapsed, "redieect >>", myResponse.is_redirect)

if not myResponse.ok:
	print("error !!!") 
	print("status " : myResponse.status_code)
	print("reason " : myResponse.reason)
	print("headers " : myResponse.headers)
	print("error >>> ", myResponse.text)
