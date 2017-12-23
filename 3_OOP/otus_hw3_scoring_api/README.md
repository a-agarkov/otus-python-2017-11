# Scoring API
### Description
According to the project task, this script should implement OOP-based HTTP API scoring service. 

### Task
Develop an HTTP API for a scoring service. A template is provided in api.py, tests in test.py.
In order to reach desired method, an API should be requested with POST, with valid JSON body to '/method' url.
Elaborate Field objects and Request objects in order to reach accomplish the task.

### API Details
***Body of a request (JSON-encoded)***

```
{
  "account": "<partner company name>", 
  "login": "<login>", 
  "method": "<method name>",
  "token": "<auth token>", 
  "arguments": {}
}
```

* account - string, optional, nullable;
* login - string, required, nullable;
* method - string, required, nullable;
* token - string, required, nullable;
* arguments - dictionary (JSON), required, nullable.

Request is deemed valid, if each request field is valid.

**Response:**

```
{
  "code": <response code>, 
  "response": {<response message>}
}
```
```
{
    "code": <response code>, 
    "error": {<error message>}
}
```

***'online_score' method***

**Arguments:**

* phone - string or integer of length 11, starts with 7, optinal, nullable;
* email - string, should contain @, optinal, nullable;
* first_name - string, optinal, nullable;
* last_name - string, optinal, nullable;
* birthday - date string, DD.MM.YYYY, age for such date should be less, than 70 years, optinal, nullable;
* gender - integers 0, 1 or 2, optinal, nullable.

Arguments are deemed valid, in case each field is valid and arguments contain any non-empty pair from the following sets:
* phone-email, 
* first name-last name, 
* gender-birthday.

**Context:** 

Context dictionary key "has" should contain non-empty fields for a response.

**Response:**

A score in range from 0 to 5 is returned:

```{"score": <float>}```

If request is sent by admin score is 42: 

```{"score": 42}```

in case there was a validation error.

```{"code": <error code>, "error": "<error message>"}```

***'clients_interests' method***

**Arguments:**

* client_ids - integer array, required, non-empty;
* date - date string DD.MM.YYYY, optional, nullable;

Arguments are deemed valid, in case each field is valid.

**Context:** 

Context dictionary key "nclients" contains number of requested client_ids.

**Response:**

Dictionary {<client_id>:[<list of interests>]}. Interests list is generated randomly.

```{"client_id1": ["interest1", "interest2"], ...}```

Errors produce response:

```{"code": <error code>, "error": "<error message>"}```

### MongoDB integration
According to further development task, an integration with key-value storage had to be implemented. 
Such storage should enhance ```store``` class, which caches scoring data and retrieves them upon calling ```get_score``` method.
MongoDB was chosen as such for its availability and support by developers community.
In order to initialize connection to local MongoDB based Cache data base the following global variables (```api.py```) are used:

* ```CACHE_DB``` - name of cache database;
* ```SCORE_CACHE_COLLECTION``` - name of collection, which contains score cache;
* ```CID_INTERESTS_COLLECTION``` - name of collection, which contains clients' interests.

Please note, that score data should expire. 
Expiration term could be passed to ```expire_after_seconds``` parameter of ```cache_set``` method. 
Default expiration term is 60 minutes.

### Test suite

Test suite features unit tests with different sets of data for all Field and Request objects, as well as tests for method handler, routing and request object processing.
According to task for Home Work 4 the following goals should be acheived:
* Develop ```case``` method, which should be used as a test method decorator. ```case``` facilitates testing of the code base with different data sets. 
* Elaborate on test fixtures. Such may include Data Base initialization and mocking data availability.

To perform tests, run from command line:

`python -m unittest tests/scoring_api_tests.py`

### Usage

Runnig script starts a server at localhost:8080. After the server has been started, you can send POST requests to /method URL-path.

Sample request is as follows:

```$ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token":"55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95","arguments": {"phone": "77777777777", "email": "jake@otus.ru", "first_name": "Jake", "last_name": "Jackson", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/```

Also, sample requests are provided in 'OTUS_HW3.postman_collection.json'.

### Code author
Алексей Агарков

slack: Alexey Agarkov (Alex_A)