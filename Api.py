from flask import Flask, jsonify, Response
from flask_classful import FlaskView, route, request
from flask_cors import CORS

from PyPSAHandler import PyPSAHandler

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello():
    return "Hello World!"

class Api(FlaskView):
    route_base = '/api/'

    @route('/calculation', methods=['POST'])
    def calculate(self):
        validationResult = PyPSAHandler.validate(request.get_json())
        if(validationResult is not None):
            return Response(validationResult, mimetype = 'text/plain', status = 406)

        handler = PyPSAHandler(request.get_json())

        calculationResult = handler.calculate()

        if(calculationResult is None):
            return Response("The submitted situation is not possible", mimetype='text/plain', status=400)
        else:
            return jsonify(calculationResult)

Api.register(app)
