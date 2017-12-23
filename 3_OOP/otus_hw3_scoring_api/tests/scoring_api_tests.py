import json
import random
import unittest

from hashlib import sha512
import datetime as dt
from time import sleep

import api
from copy import deepcopy

VALID_ADMIN_VALUE_SET = {'account': 'admin',
                         'login': 'admin',
                         'arguments': {'birthday': '01.02.1990',
                                       'email': 'asda@asda',
                                       'first_name': 'vavrew',
                                       'last_name': 'asdfewef',
                                       'gender': 1,
                                       'phone': '77777777777'}}
VALID_USER_VALUE_SET = {'account': 'horns&hoofs',
                        'login': 'h&f',
                        'token': '55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95',
                        'arguments': {'birthday': '01.02.1990',
                                      'email': 'asda@asda',
                                      'first_name': 'vavrew',
                                      'last_name': 'asdfewef',
                                      'gender': 1,
                                      'phone': '77777777777'}}


def case(data):
    def test_decorator(fn):
        def repl(self, *args):
            for i in data:
                try:
                    fn(self, i)
                except AssertionError:
                    print(f"Assertion error caught for case: {i}")
                    raise

        return repl

    return test_decorator


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = api.ScoreCache(db=api.SCORE_CACHE_DB,
                                    score_collection=api.SCORE_CACHE_COLLECTION,
                                    cid_interests_collection=api.CID_INTERESTS_COLLECTION)

        cids = ["i:%s" % i for i in range(1, 4)]
        cids_in_db = [item['_id'] for item in self.store.cid_interests_collection.find()]

        if not all(cid in cids_in_db for cid in cids):
            interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek",
                         "otus"]
            self.store.cid_interests_collection.insert_many([{'_id': i,
                                                              'interests': json.dumps(random.sample(interests, 2))}
                                                             for i in cids])

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    @staticmethod
    def make_token(admin: bool = False,
                   account: str = None,
                   login: str = None,
                   salt: str = None):
        if admin:
            return sha512(f'{dt.datetime.now().strftime("%Y%m%d%H")}{salt}'.encode()).hexdigest()
        else:
            return sha512(f'{account}{login}{salt}'.encode()).hexdigest()

    @staticmethod
    def validate_value(field_instance: object, value=None) -> bool:
        try:
            field_instance.validate(value)
            return True
        except Exception:
            return False

    @staticmethod
    def validate_request_object(object_class: object, value: dict = {}) -> bool:
        try:
            object_class(**value)
            return True
        except Exception:
            return False

    @staticmethod
    def validate_OnlineScoreRequest(object_class: object, value: dict = {}) -> bool:
        try:
            obj = object_class(**value)
            obj.validate()
            return True
        except Exception:
            return False

    @case(['sdfsd', "1231qweq", ''])
    def test_CharField_pass(self, val):
        first_name = api.CharField(required=False, nullable=True)
        self.assertTrue(self.validate_value(first_name, value=val))

    @case([None])
    def test_CharField_fail(self, val):
        first_name = api.CharField(required=False, nullable=True)
        self.assertFalse(self.validate_value(first_name, value=val))

    @case(["qweq@", "@", "@qweq"])
    def test_EmailField_pass(self, val):
        email = api.EmailField(required=False, nullable=True)
        self.assertTrue(self.validate_value(email, val))

    @case(["chocolatey", "chocolatey.at.gmail.com", "chocolatey.at.4124"])
    def test_EmailField_fail(self, val):
        email = api.EmailField(required=False, nullable=True)
        self.assertFalse(self.validate_value(email, val))

    @case(["77777777777"])
    def test_PhoneField_pass(self, val):
        phone = api.PhoneField(required=False, nullable=True)
        self.assertTrue(self.validate_value(phone, val))

    @case(["dasd", "7dasd", "7dasd3e3qwe"])
    def test_PhoneField_fail(self, val):
        phone = api.PhoneField(required=False, nullable=True)
        self.assertFalse(self.validate_value(phone, val))

    @case(["01.12.2001", '01.11.1990'])
    def test_DateField_pass(self, val):
        date = api.DateField(required=False, nullable=True)
        self.assertTrue(self.validate_value(date, val))

    @case(["01.12.201", 'fasf', -1])
    def test_DateField_fail(self, val):
        date = api.DateField(required=False, nullable=True)
        self.assertFalse(self.validate_value(date, val))

    @case(["01.12.2001"])
    def test_BirthDayField_pass(self, val):
        birthday = api.BirthDayField(required=False, nullable=True)
        self.assertTrue(self.validate_value(birthday, val))

    @case(["01.12.888", "01.12.2100"])
    def test_BirthDayField_fail(self, val):
        birthday = api.BirthDayField(required=False, nullable=True)
        self.assertFalse(self.validate_value(birthday, val))

    @case([0, 1, 2])
    def test_GenderField_pass(self, val):
        gender = api.GenderField(required=False, nullable=True)
        self.assertTrue(self.validate_value(gender, val))

    @case([4, '1'])
    def test_GenderField_fail(self, val):
        gender = api.GenderField(required=False, nullable=True)
        self.assertFalse(self.validate_value(gender, val))

    @case([[1, 2, 3], [1]])
    def test_ClientIDsField(self, val):
        client_ids = api.ClientIDsField(required=True)
        self.assertTrue(self.validate_value(client_ids, val))

    @case([[1.2, 3], [1, 2, '3'], []])
    def test_ClientIDsField(self, val):
        client_ids = api.ClientIDsField(required=True)
        self.assertFalse(self.validate_value(client_ids, val))

    @case([dict(), {'asd': 123, 'asqq': 'dsa'}])
    def test_ArgumentsField_pass(self, val):
        arguments = api.ArgumentsField(required=True, nullable=True)
        self.assertTrue(self.validate_value(arguments, val))

    @case([list(), ''])
    def test_ArgumentsField_fail(self, val):
        arguments = api.ArgumentsField(required=True, nullable=True)
        self.assertFalse(self.validate_value(arguments, val))

    @case([{'client_ids': [1, 2, 3], 'date': '01.02.2002'}])
    def test_ClientsInterestsRequest_pass(self, val):
        # Proper Request
        self.assertTrue(
            self.validate_request_object(api.ClientsInterestsRequest, val))

    @case([{'client_ids': [1, 2, 3.15], 'date': '01.02.2002'},
           {'client_ids': [1, '2', 3], 'date': '01.02.2002'}])
    def test_ClientsInterestsRequest_fail(self, val):
        # Bad Request
        self.assertFalse(
            self.validate_request_object(api.ClientsInterestsRequest, val))

    @case([
        # Proper request: Complete set of arguments
        dict(first_name="vavrew",
             last_name="asdfewef",
             email="asda@asda",
             phone="77777777777",
             birthday="01.02.1990",
             gender=1),
        # Proper request: Phone + Email
        dict(email="asda@asda", phone="77777777777"),
        # Proper request: First name + Last name
        dict(first_name="vavrew", last_name="asdfewef"),
        # Proper request: Gender + Birthday
        dict(birthday="01.02.1990", gender=1)])
    def test_OnlineScoreRequest_pass(self, value_set):
        self.assertTrue(self.validate_request_object(api.OnlineScoreRequest, value_set))

    @case([
        # Bad argument
        dict(first_name="vavrew",
             last_name="asdfewef",
             email='bad_email',
             phone="77777777777",
             birthday="01.02.1990",
             gender=1),
        # Missing fields
        dict(last_name="asdfewef",
             email='asda@asda',
             birthday="01.02.1990")])
    def test_OnlineScoreRequest_fail(self, value_set):
        self.assertFalse(self.validate_request_object(api.OnlineScoreRequest, value_set))

    @case([VALID_USER_VALUE_SET,
           VALID_ADMIN_VALUE_SET])
    def test_check_valid_auth_pass(self, val):
        value_set = deepcopy(val)
        value_set['method'] = '--'

        if value_set['login'] == api.ADMIN_LOGIN:
            value_set['token'] = self.make_token(admin=True,
                                                 salt=api.ADMIN_SALT)

        good_request_object = api.MethodRequest(**value_set)
        self.assertTrue(api.check_auth(good_request_object))

    @case([VALID_USER_VALUE_SET,
           VALID_ADMIN_VALUE_SET])
    def test_check_invalid_auth_fail(self, val):
        value_set = deepcopy(val)
        value_set['method'] = '--'
        value_set['token'] = 'invalid_token'

        bad_request_object = api.MethodRequest(**value_set)
        self.assertFalse(api.check_auth(bad_request_object))

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    def test_get_score(self):
        full_set_of_arguments = dict(first_name="vavrew",
                                     last_name="asdfewef",
                                     email="asda@asda",
                                     phone="77777777777",
                                     birthday="01.02.1990",
                                     gender=1)

        score_request = api.OnlineScoreRequest(**full_set_of_arguments)

        zero_set_score = api.get_score(store=self.store, phone=None, email=None)
        self.assertEquals(zero_set_score, 0)

        only_email_score = api.get_score(store=self.store, phone=None,
                                         email=score_request.email)
        self.assertEquals(only_email_score, 1.5)

        only_phone_score = api.get_score(store=self.store, email=None,
                                         phone=score_request.phone)
        self.assertEquals(only_phone_score, 1.5)

        phone_email_score = api.get_score(store=self.store,
                                          email=score_request.email,
                                          phone=score_request.phone)
        self.assertEquals(phone_email_score, 3)

        birthday_gender_set_score = api.get_score(store=self.store, phone=None, email=None,
                                                  birthday=score_request.birthday,
                                                  gender=score_request.gender)
        self.assertEquals(birthday_gender_set_score, 1.5)

        first_name_last_name_set_score = api.get_score(store=self.store, phone=None, email=None,
                                                       first_name=score_request.first_name,
                                                       last_name=score_request.last_name)
        self.assertEquals(first_name_last_name_set_score, 0.5)

        max_set_score = api.get_score(store=self.store,
                                      first_name=score_request.first_name + "key_altering_string",
                                      last_name=score_request.last_name,
                                      email=score_request.email,
                                      phone=score_request.phone,
                                      birthday=score_request.birthday,
                                      gender=score_request.gender)
        self.assertEquals(max_set_score, 0.5 + 1.5 + 1.5 + 1.5)

    @case([VALID_USER_VALUE_SET,
           VALID_ADMIN_VALUE_SET])
    def test_online_score_pass(self, val):
        value_set = deepcopy(val)
        value_set['method'] = 'online_score'
        if value_set['login'] == api.ADMIN_LOGIN:
            value_set['token'] = self.make_token(admin=True,
                                                 salt=api.ADMIN_SALT)

        request_object = api.MethodRequest(**value_set)
        score, code = api.online_score(request_object, ctx=dict(), store=self.store)
        self.assertIsInstance(score, dict)
        self.assertTrue('score' in score.keys())
        self.assertEquals(code, api.OK)

    @case([dict()])
    def test_online_score_fail(self, value_set):
        bad_score, code = api.online_score(request=value_set, ctx=dict(), store=self.store)
        self.assertEquals(code, api.INVALID_REQUEST)
        self.assertIsInstance(bad_score, str)

    def test_get_clients_interests(self):
        self.assertTrue(api.get_interests(store=self.store, cid=1))
        self.assertEquals(len(api.get_interests(store=self.store, cid=1)), 2)

    @case([VALID_USER_VALUE_SET,
           VALID_ADMIN_VALUE_SET])
    def test_clients_interests_pass(self, val):
        value_set = deepcopy(val)
        value_set['method'] = "clients_interests"
        value_set['arguments'] = {'client_ids': [1, 2, 3], 'date': '01.02.2002'}
        if value_set['login'] == api.ADMIN_LOGIN:
            value_set['token'] = self.make_token(admin=True,
                                                 salt=api.ADMIN_SALT)

        request_object = api.MethodRequest(**value_set)
        interests, code = api.clients_interests(request_object,
                                                ctx=dict(),
                                                store=self.store)
        self.assertIsInstance(interests, dict)

        # all client_ids are present in response
        self.assertTrue(all(cid in interests.keys() for cid in value_set['arguments']['client_ids']))

        # all client interests are length 2
        self.assertTrue(all(len(interests_set) == 2 for interests_set in interests.values()))

        # response code is OK
        self.assertEquals(code, api.OK)

    @case([dict()])
    def test_clients_interests_fail(self, value_set):
        bad_resp, code = api.clients_interests(request=value_set, ctx=dict(), store=self.store)
        self.assertEquals(code, api.INVALID_REQUEST)
        self.assertIsInstance(bad_resp, str)

    @case([VALID_USER_VALUE_SET])
    def test_method_handler(self, val):
        value_set = deepcopy(val)
        value_set['method'] = 'online_score'

        resp, code = api.method_handler({"body": value_set,
                                         "headers": dict()}, dict(), store=self.store)
        self.assertIsInstance(resp, dict)
        self.assertTrue('score' in resp.keys())
        self.assertEquals(code, api.OK)

        resp, code = api.method_handler({"body": None,
                                         "headers": dict()}, dict(), store=self.store)
        self.assertIsInstance(resp, str)
        self.assertEquals(code, api.INVALID_REQUEST)

        value_set['method'] = 'absent_method'
        resp, code = api.method_handler({"body": value_set,
                                         "headers": dict()}, dict(), store=self.store)
        self.assertIsInstance(resp, str)
        self.assertTrue("not found" in resp)
        self.assertEquals(code, api.NOT_FOUND)

        value_set['token'] = 'bad_token'
        resp, code = api.method_handler({"body": value_set,
                                         "headers": dict()}, dict(), store=self.store)
        self.assertIsInstance(resp, str)
        self.assertEquals(resp, "Forbidden")
        self.assertEquals(code, api.FORBIDDEN)

    # def test_score_cache(self):
    #     key = 'some key'
    #     self.store.cache_set(key=key,
    #                          value=5,
    #                          expire_after_seconds=3,
    #                          collection='score_collection',
    #                          target_value_name='score')
    #     stored_value = self.store.cache_get(key,
    #                                         collection='score_collection',
    #                                         target_value_name='score')
    #     self.assertIsNotNone(stored_value)
    #     sleep(60)
    #     stored_value = self.store.cache_get(key,
    #                                         collection='score_collection',
    #                                         target_value_name='score')
    #     self.assertIsNone(stored_value)
    #

if __name__ == "__main__":
    unittest.main()
