"""
Example script that shows how to send external synthetic data into Dynatrace.
"""
from __future__ import print_function
import requests, time
import logging
import os
import json

# Dynatrace Tenant URL, Credentials, and configuration
YOUR_DT_API_URL = '<YOUR TENANT URL HERE>' #For Dynatrace Managed use https://{owndomain}/e/{id}
YOUR_DT_API_TOKEN = '<YOUR SYNTHETIC API TOKEN HERE>'  #Settings->Integration->Dynatrace API->Generate Token
URL_TO_TEST = '<YOUR URL TO TEST HERE>' # http://www.example.com/health
SYNTH_ENGINE_NAME = '<TEST ENGINE NAME HERE>' # eg: 'Python Script' or 'Selenium'
SYNTH_TEST_TITLE = '<TEST NAME HERE>' # eg: 'API Endpoint Test'
SYNTH_TEST_STEP_TITLE = '<TEST STEP TITLE HERE>' # eg: 'testing api endpoint health'

# Synthetic Test
syntheticRequest = requests.get(URL_TO_TEST)
responseTime = syntheticRequest.elapsed.total_seconds()

# configuring synthetic test result
success = False
if (syntheticRequest.status_code == requests.codes.ok):
    success = True

print ('Synthetic request - Response time:' + str(responseTime) + 's Status code:' + str(syntheticRequest.status_code) + " Success:" + str(success))

timestamp = round(time.time() * 1000)

# Payload to post to Dynatrace Endpoint
payload = {
    "messageTimestamp": timestamp,
    "syntheticEngineName": SYNTH_ENGINE_NAME,
    "syntheticEngineIconUrl": "http://assets.dynatrace.com/global/icons/cpu_processor.png",
    "locations": [{
         "id": "1",
         "name": "Waltham"
    }],
    "tests" : [ {
        "id": "3",
        "title": SYNTH_TEST_TITLE,
        "testSetup":  "Python script",
        "drilldownLink": URL_TO_TEST,
        "enabled": True,
        "locations": [ {
            "id": "1",
            "enabled": True
        }],
        "steps": [ {
            "id": 1,
            "title": SYNTH_TEST_STEP_TITLE
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
}]}

headers = {'content-type': 'application/json'}
r = requests.post(YOUR_DT_API_URL + '/api/v1/synthetic/ext/tests?Api-Token=' + YOUR_DT_API_TOKEN, json=payload, headers=headers)
print('Post Synthetic Payload Status:' + str(r.status_code))

# Event Management
# Do we have a current open problem
problemEventId = None
problemStatus = None

r = requests.get(YOUR_DT_API_URL + '/api/v1/problem/feed?Api-Token=' + YOUR_DT_API_TOKEN, headers=headers)
decoded = json.loads(r.content)
for problem in decoded['result']['problems']:
        for rankedImpact in problem['rankedImpacts']:
            if problem['status'] == "OPEN" and rankedImpact['entityName'] == SYNTH_TEST_TITLE:
                try:
                    problemEventId = str(problem['id'])
                except (NameError, ValueError, KeyError, TypeError):
                    print('No Open Problem Event')
                    problemEventId = timestamp
                    print('problem event id from timestamp:' + str(problemEventId))
                else:
                    problemStatus = problem['status']     

if (problemEventId is None):
    problemEventId = timestamp
    print('problemEventId not defined, using timestamp: ' + str(problemEventId))

# No Problems, clear existing event:
if success == True:
    if problemStatus == "OPEN":
        print('Open problem ID ' + str(problemEventId) + ' will expire in 15 mins')
## The following section does not work correctly.  Workaround is current problem will expire after 15mins if not refreshed
#        payload = {
#        "syntheticEngineName" : "My test",
#        "open": [],
#        "resolved": [{
#            "testId": "3",
#            "eventId": problemEventId,
#            "endIntervalMin": {timestamp()},
#            "endIntervalMax": {timestamp()}
#        }]
#     }
#        r = requests.post(YOUR_DT_API_URL + '/api/v1/synthetic/ext/events?Api-Token=' + YOUR_DT_API_TOKEN, json=payload, headers=headers)
#        print('Post Resolved Status:' + str(r.status_code) + ' ProblemID:' + str(problemEventId) + 'Message: ' + str(r.text))
#        print('Current Problem ID (from True): ' + str(problemEventId))         
#        print(problem['startTime'])
    else:
        print('Success (True) and no open problem')

if success == False:

    payload = {
        "syntheticEngineName": "My test",
        "open": [{
            "testId": "3",
            "name": "My Outage Event",
            "eventId" : problemEventId,
            "eventType": "testOutage",
            "reason": "This is a simulated Outage",
            "startTimestamp": timestamp,
            "timeoutTimeframeInMillis": 60000,
            "locationIds" : ["1"]
            }]
    }
    r = requests.post(YOUR_DT_API_URL + '/api/v1/synthetic/ext/events?Api-Token=' + YOUR_DT_API_TOKEN, json=payload, headers=headers)
    print('Post Open Status:' + str(r.status_code) + ' ProblemID: (from False) ' + str(problemEventId))