"""
Example script that shows how to send external synthetic data into Dynatrace.
"""
import requests, time
import logging
import os

YOUR_DT_API_URL = 'https://uji38866.live.dynatrace.com'; #For Dynatrace Managed use https://{owndomain}/e/{id}
YOUR_DT_API_TOKEN = 'oWo12TQESsib2zijzm0N3';

URL_TO_TEST = 'http://demo2482444.mockable.io/health';

syntheticRequest = requests.get(URL_TO_TEST);
responseTime = syntheticRequest.elapsed.total_seconds();

success = False;
if (syntheticRequest.status_code == requests.codes.ok):
    success = True;

print ('Synthetic request - Response time:' + str(responseTime) + 's Status code:' + str(syntheticRequest.status_code) + " Success:" + str(success));

timestamp = time.time() * 1000;

payload = {
    "messageTimestamp": timestamp,
    "syntheticEngineName": "My test",
    "syntheticEngineIconUrl": "http://assets.dynatrace.com/global/icons/cpu_processor.png",
    "locations": [{
         "id": "1",
         "name": "Waltham"
    }],
    "tests" : [ {
        "id": "3",
        "title": "mockable.io",
        "testSetup":  "Python script",
        "drilldownLink": "http://demo2482444.mockable.io/health",
        "enabled": True,
        "locations": [ {
            "id": "1",
            "enabled": True
        }],
        "steps": [ {
            "id": 1,
            "title": "Get request mockable.io"
        }]
    }],
    "testResults": [{
        "id": "3",
        "scheduleIntervalInSeconds": 60,
        "totalStepCount": 1,
        "locationResults": [{
            "id": "1",
            "startTimestamp": timestamp,
            "success": success,
            "stepResults": [{
                "id" : 1,
                "startTimestamp": timestamp,
                "responseTimeMillis": responseTime * 1000
            }]
    }]
}]};

headers = {'content-type': 'application/json'}
r = requests.post(YOUR_DT_API_URL + '/api/v1/synthetic/ext/tests?Api-Token=' + YOUR_DT_API_TOKEN, json=payload, headers=headers)
# Output API response
print(r)
print(r.text)
osfileslashes = "/"
stateFileName = os.path.dirname(os.path.abspath(__file__)) + osfileslashes + "openproblem.txt"

if success == True:
    # lets figure out if we currently have an open problem - if SO - CLOSE IT
    if os.path.exists(stateFileName): 
        stateFile = open(stateFileName, "r");
        currentState = stateFile.read();
        stateFile.close()
        if str.startswith(currentState, "open"):
		    # we need to close the problem and update file
            currentProblemId = currentState[5:]
#            payload = {
#                "syntheticEngineName" : "My test",
#                "resolved": [
#					{
#					"testId": "3",
#					"eventId": currentProblemId,
#                   "endIntervalMin": startTimestamp,
#                  "endIntervalMax": timestamp
#					}
#				]
#           }
            r = requests.post(YOUR_DT_API_URL + '/api/v1/synthetic/ext/events?Api-Token=' + YOUR_DT_API_TOKEN, json=payload, headers=headers)
            print(r)
            print(r.text)
            stateFile = open(stateFileName, "w")
            stateFile.write(currentProblemId)
            stateFile.close()
			
if success == False:
    # we have to figure out if a problem is already open - if so - do nothing
    nextProblemEventId = 1;
    createProblem = True;
    if os.path.exists(stateFileName):
        stateFile = open(stateFileName, "r")
        currentState = stateFile.read()
        stateFile.close()
        if str.startswith(currentState, "open"):
			# we dont do anything because we have an open problem
            createProblem = False
        else:
            # no current open problem. parse the problem id out of the file which is the previous problem id we used
            if len(currentState) > 0:
                nextProblemEventId = int(currentState) + 1
                createProblem = True
            
    if createProblem:
        payload = {
        "syntheticEngineName": "My test",
        "open": [
            {
                "testId": "3",
                "eventId": str(nextProblemEventId),
                "name": "MySampleEvent",
                "eventType": "testOutage",
                "reason": "This is a simulated Outage",
                "startTimestamp": timestamp,
                "timeoutTimeframeInMillis": 60000,
                "locationIds" : ["1"]
            }
            ]
        }
        r = requests.post(YOUR_DT_API_URL + '/api/v1/synthetic/ext/events?Api-Token=' + YOUR_DT_API_TOKEN, json=payload, headers=headers)
        print(r)
        print(r.text)
  
        # keep track of state: next time we have an error dont open another problem
        stateFile = open(stateFileName, "w")
        stateFile.write("open: " + str(nextProblemEventId))
        stateFile.close()
