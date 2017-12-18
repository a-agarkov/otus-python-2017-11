import unittest

from hashlib import sha512
import datetime as dt
import api
from copy import deepcopy


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

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

    def test_CharField(self):
        first_name = api.CharField(required=False, nullable=True)

        self.assertTrue(self.validate_value(first_name, value='sdfsd'))
        self.assertFalse(self.validate_value(first_name, value=None))

    def test_EmailField(self):
        email = api.EmailField(required=False, nullable=True)

        self.assertTrue(self.validate_value(email, "qweq@"))
        self.assertFalse(self.validate_value(email, "chocolatey"))

    def test_PhoneField(self):
        phone = api.PhoneField(required=False, nullable=True)

        self.assertTrue(self.validate_value(phone, "77777777777"))
        self.assertFalse(self.validate_value(phone, "dasd"))
        self.assertFalse(self.validate_value(phone, "7dasd"))
        self.assertFalse(self.validate_value(phone, "7dasd3e3qwe"))

    def test_DateField(self):
        date = api.DateField(required=False, nullable=True)

        self.assertTrue(self.validate_value(date, "01.12.2001"))
        self.assertFalse(self.validate_value(date, "01.12.201"))
        self.assertFalse(self.validate_value(date, 'fasf'))
        self.assertFalse(self.validate_value(date, -1))

    def test_BirthDayField(self):
        birthday = api.BirthDayField(required=False, nullable=True)

        self.assertTrue(self.validate_value(birthday, "01.12.2001"))
        self.assertFalse(self.validate_value(birthday, "01.12.888"))
        self.assertFalse(self.validate_value(birthday, "01.12.2100"))

    def test_GenderField(self):
        gender = api.GenderField(required=False, nullable=True)

        self.assertTrue(self.validate_value(gender, 0))
        self.assertTrue(self.validate_value(gender, 1))
        self.assertTrue(self.validate_value(gender, 2))
        self.assertFalse(self.validate_value(gender, 4))
        self.assertFalse(self.validate_value(gender, '1'))

    def test_ClientIDsField(self):
        client_ids = api.ClientIDsField(required=True)

        self.assertTrue(self.validate_value(client_ids, [1, 2, 3]))
        self.assertFalse(self.validate_value(client_ids, [1.2, 3]))
        self.assertFalse(self.validate_value(client_ids, [1, 2, '3']))
        self.assertFalse(self.validate_value(client_ids, []))

    def test_ArgumentsField(self):
        arguments = api.ArgumentsField(required=True, nullable=True)

        self.assertTrue(self.validate_value(arguments, dict()))
        self.assertFalse(self.validate_value(arguments, list()))
        self.assertFalse(self.validate_value(arguments, ''))

    def test_ClientsInterestsRequest(self):
        # Proper Request
        self.assertTrue(
            self.validate_request_object(api.ClientsInterestsRequest,
                                         {'client_ids': [1, 2, 3],
                                          'date': '01.02.2002'}))
        # Bad Request
        self.assertFalse(
            self.validate_request_object(api.ClientsInterestsRequest,
                                         {'client_ids': [1, 2, 3.15],
                                          'date': '01.02.2002'}))

    def test_OnlineScoreRequest(self):
        # Proper request: Complete set of arguments
        full_set_of_arguments = dict(first_name="vavrew",
                                     last_name="asdfewef",
                                     email="asda@asda",
                                     phone="77777777777",
                                     birthday="01.02.1990",
                                     gender=1)
        self.assertTrue(
            self.validate_request_object(api.OnlineScoreRequest,
                                         full_set_of_arguments))

        # Proper request: Phone + Email
        partial_set_of_arguments = dict(email="asda@asda",
                                        phone="77777777777")
        api.OnlineScoreRequest(**partial_set_of_arguments)
        self.assertTrue(
            self.validate_request_object(api.OnlineScoreRequest,
                                         partial_set_of_arguments))

        # Proper request: First name + Last name
        partial_set_of_arguments = dict(first_name="vavrew",
                                        last_name="asdfewef")
        self.assertTrue(
            self.validate_request_object(api.OnlineScoreRequest,
                                         partial_set_of_arguments))

        # Proper request: Gender + Birthday
        partial_set_of_arguments = dict(birthday="01.02.1990",
                                        gender=1)
        self.assertTrue(
            self.validate_request_object(api.OnlineScoreRequest,
                                         partial_set_of_arguments))

        # Bad argument
        bad_arguments = deepcopy(full_set_of_arguments)
        bad_arguments['email'] = 'bad_email'
        self.assertFalse(
            self.validate_request_object(api.OnlineScoreRequest,
                                         bad_arguments))

        # Missing fields
        incomplete_set_of_arguments = deepcopy(full_set_of_arguments)
        for missing_field in ["phone", "first_name", "gender"]:
            del incomplete_set_of_arguments[missing_field]

        self.assertFalse(
            self.validate_OnlineScoreRequest(api.OnlineScoreRequest,
                                             incomplete_set_of_arguments))

    def test_check_auth(self):
        # valid user token
        hoofs_n_horns_req = {'account': 'horns&hoofs',
                             'login': 'h&f',
                             'arguments': {},
                             'method': "--"}
        hoofs_n_horns_req['token'] = self.make_token(admin=False,
                                                     account=hoofs_n_horns_req['account'],
                                                     login=hoofs_n_horns_req['login'],
                                                     salt=api.SALT)

        good_request_object = api.MethodRequest(**hoofs_n_horns_req)
        self.assertTrue(api.check_auth(good_request_object))

        # invalid user token
        hoofs_n_horns_req['token'] = 'invalid_token'
        bad_request_object = api.MethodRequest(**hoofs_n_horns_req)

        self.assertFalse(api.check_auth(bad_request_object))

        # valid admin token
        admin_req = {'account': 'admin',
                     'login': 'admin',
                     'arguments': {},
                     'method': "--",
                     'token': self.make_token(admin=True,
                                              salt=api.ADMIN_SALT)}
        good_admin_request = api.MethodRequest(**admin_req)
        self.assertTrue(api.check_auth(good_admin_request))

        # invalid admin token
        admin_req['token'] = 'invalid_admin_token'
        bad_admin_request = api.MethodRequest(**admin_req)
        self.assertFalse(api.check_auth(bad_admin_request))

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

        zero_set_score = api.get_score(store=None, phone=None, email=None)
        self.assertEquals(zero_set_score, 0)

        only_email_score = api.get_score(store=None, phone=None,
                                         email=score_request.email)
        self.assertEquals(only_email_score, 1.5)

        only_phone_score = api.get_score(store=None, email=None,
                                         phone=score_request.phone)
        self.assertEquals(only_phone_score, 1.5)

        phone_email_score = api.get_score(store=None,
                                          email=score_request.email,
                                          phone=score_request.phone)
        self.assertEquals(phone_email_score, 3)

        birthday_gender_set_score = api.get_score(store=None, phone=None, email=None,
                                                  birthday=score_request.birthday,
                                                  gender=score_request.gender)
        self.assertEquals(birthday_gender_set_score, 1.5)

        first_name_last_name_set_score = api.get_score(store=None, phone=None, email=None,
                                                       birthday=score_request.birthday,
                                                       gender=score_request.gender)
        self.assertEquals(first_name_last_name_set_score, 1.5)

        max_set_score = api.get_score(store=None,
                                      first_name=score_request.first_name,
                                      last_name=score_request.last_name,
                                      email=score_request.email,
                                      phone=score_request.phone,
                                      birthday=score_request.birthday,
                                      gender=score_request.gender)
        self.assertEquals(max_set_score, 0.5 + 1.5 + 1.5 + 1.5)

    def test_online_score(self):
        ho_n_ho_req = {'account': 'horns&hoofs',
                       'login': 'h&f',
                       'arguments': {'birthday': '01.02.1990',
                                     'email': 'asda@asda',
                                     'first_name': 'vavrew',
                                     'gender': 1,
                                     'last_name': 'asdfewef',
                                     'phone': '77777777777'},
                       'method': "online_score"}

        ho_n_ho_req['token'] = self.make_token(admin=False,
                                               account=ho_n_ho_req['account'],
                                               login=ho_n_ho_req['login'],
                                               salt=api.SALT)

        ho_n_ho_request_object = api.MethodRequest(**ho_n_ho_req)

        score, code = api.online_score(ho_n_ho_request_object, ctx=dict(), store=None)

        self.assertIsInstance(score, dict)
        self.assertTrue('score' in score.keys())
        self.assertEquals(score['score'], 5)
        self.assertEquals(code, api.OK)

        admin_req = {'account': 'admin',
                     'login': 'admin',
                     'arguments': {'birthday': '01.02.1990',
                                   'email': 'asda@asda',
                                   'first_name': 'vavrew',
                                   'gender': 1,
                                   'last_name': 'asdfewef',
                                   'phone': '77777777777'},
                     'method': "online_score",
                     'token': self.make_token(admin=True,
                                              salt=api.ADMIN_SALT)}

        admin_request_object = api.MethodRequest(**admin_req)

        score, code = api.online_score(admin_request_object, ctx=dict(), store=None)

        self.assertIsInstance(score, dict)
        self.assertTrue('score' in score.keys())
        self.assertEquals(score['score'], 42)
        self.assertEquals(code, api.OK)

        bad_score, code = api.online_score(request=dict(), ctx=dict(), store=None)

        self.assertEquals(code, api.INVALID_REQUEST)
        self.assertIsInstance(bad_score, str)

    def test_get_clients_interests(self):
        self.assertTrue(api.get_interests(store=None, cid=1))
        self.assertEquals(len(api.get_interests(store=None, cid=1)), 2)

    def test_clients_interests(self):
        client_ids = [1, 2, 3]
        ho_n_ho_req = {'account': 'horns&hoofs',
                       'login': 'h&f',
                       'arguments': {'date': '01.01.2000',
                                     'client_ids': client_ids},
                       'method': "clients_interests"}

        ho_n_ho_req['token'] = self.make_token(admin=False,
                                               account=ho_n_ho_req['account'],
                                               login=ho_n_ho_req['login'],
                                               salt=api.SALT)

        ho_n_ho_request_object = api.MethodRequest(**ho_n_ho_req)

        interests, code = api.clients_interests(ho_n_ho_request_object,
                                                ctx=dict(),
                                                store=None)

        # response is a dictionary
        self.assertIsInstance(interests, dict)

        # all client_ids are present in response
        self.assertTrue(all(cid in interests.keys() for cid in client_ids))

        # retrieved 2 interests for each client_id
        self.assertTrue(all(len(interests[cid]) == 2 for cid in client_ids))

        # response code is OK
        self.assertEquals(code, api.OK)

        bad_resp, code = api.clients_interests(request=dict(), ctx=dict(), store=None)

        self.assertEquals(code, api.INVALID_REQUEST)
        self.assertIsInstance(bad_resp, str)

    def test_method_handler(self):
        ho_n_ho_req = {'account': 'horns&hoofs',
                       'login': 'h&f',
                       'arguments': {'birthday': '01.02.1990',
                                     'email': 'asda@asda',
                                     'first_name': 'vavrew',
                                     'gender': 1,
                                     'last_name': 'asdfewef',
                                     'phone': '77777777777'},
                       'method': "online_score"}

        ho_n_ho_req['token'] = self.make_token(admin=False,
                                               account=ho_n_ho_req['account'],
                                               login=ho_n_ho_req['login'],
                                               salt=api.SALT)

        resp, code = api.method_handler({"body": ho_n_ho_req,
                                         "headers": dict()}, dict(), None)
        self.assertIsInstance(resp, dict)
        self.assertTrue('score' in resp.keys())
        self.assertEquals(resp['score'], 5)
        self.assertEquals(code, api.OK)

        resp, code = api.method_handler({"body": None,
                                         "headers": dict()}, dict(), None)
        self.assertIsInstance(resp, str)
        self.assertEquals(code, api.INVALID_REQUEST)

        ho_n_ho_req['method'] = 'absent_method'
        resp, code = api.method_handler({"body": ho_n_ho_req,
                                         "headers": dict()}, dict(), None)
        self.assertIsInstance(resp, str)
        self.assertTrue("not found" in resp)
        self.assertEquals(code, api.NOT_FOUND)

        ho_n_ho_req['token'] = 'bad_token'
        resp, code = api.method_handler({"body": ho_n_ho_req,
                                         "headers": dict()}, dict(), None)
        self.assertIsInstance(resp, str)
        self.assertEquals(resp, "Forbidden")
        self.assertEquals(code, api.FORBIDDEN)

