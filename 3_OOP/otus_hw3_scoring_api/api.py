#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime as dt
import logging
from hashlib import sha512
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from abc import ABCMeta, abstractmethod
from scoring import get_score, get_interests

from store import CACHE_DB, SCORE_CACHE_COLLECTION, CID_INTERESTS_COLLECTION, CacheStore

utcnow = dt.datetime.utcnow

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class ValidationError(Exception):
    pass


class BaseRequestField(object):
    """
    Base class for fields. Defines name and initialization parameters.
    Params:
    'required' - defines if an instantiated field is required for request;
    'nullable' - defines if an instantiated field could be empty.
    """
    __metaclass__ = ABCMeta

    def __init__(self, required: bool = False, nullable: bool = False):
        # self.name = None
        self.required = required
        self.nullable = nullable

    # # updates fields
    # def __set__(self, instance, value):
    #     field_name = '__' + self.name
    #     setattr(instance, field_name, value)
    # todo: нужно сделать возможность сначала писать в Field данные без предварительной валидации, а затем вызывать валидацию явно.

    @abstractmethod
    def validate(self, value):
        raise NotImplementedError


class CharField(BaseRequestField):
    """
    Character field should be string.
    """

    def validate(self, value):
        if not isinstance(value, str):
            raise ValidationError('Character field should be of type "str".')


class ArgumentsField(BaseRequestField):
    """
    Arguments field should be a dictionary.
    """

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError('Arguments field should be of type "dict".')


class EmailField(CharField):
    """
    E-mail field is deemed valid only if it contains '@' symbol.
    """

    def validate(self, value):
        super(EmailField, self).validate(value)
        if not value.__contains__('@'):
            raise ValidationError('Invalid e-mail.')


class PhoneField(BaseRequestField):
    """
    Phone number should:
     - be a string or an integer;
     - consist of 11 digits;
     - start with 7.
    """

    def validate(self, value):
        if not isinstance(value, (int, str)):
            raise ValidationError('Phone field should be of type "str" or "int".')
        if not str(value).startswith('7'):
            raise ValidationError('Only phones, starting with "7", are accepted.')
        if len(str(value)) != 11:
            raise ValidationError('Phone should be 11 digits long.')
        if not all(digit.isdigit() for digit in str(value)):
            raise ValidationError('All elements of the phone number should be digits.')


class DateField(CharField):
    """
    Date should be provided in DD.MM.YYYY format.
    """

    def validate(self, value):
        super(DateField, self).validate(value)
        try:
            dt.datetime.strptime(value, '%d.%m.%Y')
        except:
            raise ValidationError("Incorrect date format. Date should be a DD.MM.YYYY string.")


class BirthDayField(DateField):
    """
    Ages over 70 are not allowed for whatever reason.
    """

    def validate(self, value):
        super(BirthDayField, self).validate(value)
        if not (0 < (dt.datetime.now() - dt.datetime.strptime(value, '%d.%m.%Y')).days / 365 <= 70):
            raise ValidationError("A request has gracefully failed in an orderly shutdown process "
                                  "due to age related restrictions.")


class GenderField(BaseRequestField):
    """
    Only three genders are allowed: male (1), female (2) and unknown (0). Integers only.
    """

    def validate(self, value):
        if any([not isinstance(value, int),
                value not in GENDERS]):
            raise ValidationError('Integer value required. Only 0, 1, 2 allowed.')


class ClientIDsField(BaseRequestField):
    """
    ClientIDs should be a non-empty list of integers.
    """

    def validate(self, value):
        if not isinstance(value, list):
            raise ValidationError('Object of type "list" required.')
        if not all(isinstance(item, int) for item in value):
            raise ValidationError('All elements of a ClientID list should be integers.')
        if not value:
            raise ValidationError('Empty lists not allowed.')


class MetaRequest(type):
    """
    Meta request class, which collects all field classes and moves them into 'fields' attribute.
    """

    def __new__(cls, name, bases, attrs):
        current_fields = {}
        for field_name, field in list(attrs.items()):
            # if passed argument is a field (BaseRequestField)
            if isinstance(field, BaseRequestField):
                # extracts field names and values from attrs (same as keyword arguments)
                field.name = field_name
                current_fields[field_name] = field
                # pop attributes to ensure all fields are kept only in .fields attr
                attrs.pop(field_name)

        new_class = super(MetaRequest, cls).__new__(cls, name, bases, attrs)
        new_class.fields = current_fields
        return new_class


class BaseRequest(object, metaclass=MetaRequest):
    """
    Base request class.
    """

    def __init__(self, **passed_fields):
        self.bad_fields = {}
        self.passed_fields_collector = []

        for field_name, value in passed_fields.items():
            setattr(self, field_name, value)
            self.passed_fields_collector.append(field_name)

    def validate(self):
        for field_name, field in self.fields.items():
            if all([field_name not in self.passed_fields_collector,
                    field.required]):
                self.bad_fields[field_name] = f'Required field {field_name} is missing.'
                continue

            field_value = getattr(self, field_name, None)

            if not field.nullable and not field_value:
                self.bad_fields[field_name] = f'Field {field_name} cannot be empty.'
                continue

            if not field.required and not field_value:
                continue

            try:
                self.fields[field_name].validate(field_value)
            except ValidationError as e:
                self.bad_fields[field_name] = (
                    f'Value {field_value} cannot be set for field "{field_name}". Error: {e}.')


class ClientsInterestsRequest(BaseRequest):
    """
    This class is used to instantiate a request object for Clients Interests request method.
    """
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    """
    This class is used to instantiate a request object for Online Score request method.
    Validation procedure checks if required parameters are present in 'arguments' dict.
    """
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    @property
    def non_empty_fields(self):
        return {key for key, value in self.__dict__.items() if value}

    def validate(self):
        super().validate()
        if not any(pair.issubset(self.non_empty_fields) for pair in [{"phone", "email"},
                                                                     {"first_name", "last_name"},
                                                                     {"gender", "birthday"}]):
            raise ValueError('Arguments should contain either of the following pairs:\n'
                             '            * phone+email,\n'
                             '            * first_name+last_name,\n'
                             '            * gender+birthday.')


class MethodRequest(BaseRequest):
    """
    This class is used to instantiate initial request object.
    """
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request: MethodRequest) -> bool:
    """
    Authenticates request.
    If admin's login provided, then admin's salt is used to authenticate.

    :param request: valid MethodRequest object.
    :return: True or False, depending on authentication result.
    """

    if request.is_admin:
        byte_encoded_str = f'{dt.datetime.now().strftime("%Y%m%d%H")}{ADMIN_SALT}'.encode()
    else:
        byte_encoded_str = f'{request.account}{request.login}{SALT}'.encode()

    digest = sha512(byte_encoded_str).hexdigest()

    return digest == request.token


def method_handler(request: dict, ctx: dict, store) -> tuple:
    """
    Method handler unpacks body of request and constructs a MethodRequest object,
    checks if request is authorized,
    and, if requested method is implemented, calls it with given params.

    :param request: request body as dict
    :param ctx: list of non-empty fields in request body
    :param store: --
    :return: response message, response code.
    """
    methods = {"online_score": online_score,
               "clients_interests": clients_interests}

    try:
        request = MethodRequest(**request.get('body', None))
        request.validate()
    except Exception as e:
        return f'{e}', INVALID_REQUEST

    if request.bad_fields:
        return f'{request.bad_fields}', INVALID_REQUEST

    if not check_auth(request):
        return "Forbidden", FORBIDDEN

    if request.method in methods.keys():
        return methods[request.method](request, ctx, store)
    else:
        return f"Method {request.method} not found.", NOT_FOUND


def online_score(request, ctx, store):
    try:
        score_request = OnlineScoreRequest(**request.arguments)
    except Exception as e:
        return f'{e}', INVALID_REQUEST

    ctx['has'] = score_request.non_empty_fields

    if request.is_admin:
        return {'score': 42}, OK

    response = {'score': get_score(store=store,
                                   first_name=score_request.first_name,
                                   last_name=score_request.last_name,
                                   email=score_request.email,
                                   phone=score_request.phone,
                                   birthday=score_request.birthday,
                                   gender=score_request.gender)}
    return response, OK


def clients_interests(request, ctx, store):
    try:
        interests_requests = ClientsInterestsRequest(**request.arguments)
    except Exception as e:
        return f'{e}', INVALID_REQUEST

    client_ids = set(interests_requests.client_ids)

    ctx['nclients'] = len(client_ids)

    response = {client_id: get_interests(store, client_id) for client_id in client_ids}

    return response, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    """
    Server.
    """
    router = {"method": method_handler}
    store = CacheStore(db=CACHE_DB,
                       score_collection=SCORE_CACHE_COLLECTION,
                       cid_interests_collection=CID_INTERESTS_COLLECTION)

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        if not code:
            code = INVALID_REQUEST

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}

        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode())
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
