import os
import json
import pickle
import joblib
import pandas as pd
from flask import Flask, jsonify, request
from peewee import (
    SqliteDatabase, PostgresqlDatabase, Model, IntegerField,
    FloatField, TextField, IntegrityError
)
from playhouse.shortcuts import model_to_dict
from uuid import uuid4

########################################
# Begin database stuff

DB = SqliteDatabase('predictions.db')


class Prediction(Model):
    observation_id = IntegerField(unique=True)
    observation = TextField()
    proba = FloatField()
    true_class = IntegerField(null=True)

    class Meta:
        database = DB


DB.create_tables([Prediction], safe=True)

# End database stuff
########################################

########################################
# Unpickle the previously-trained model


with open(os.path.join('columns.json')) as fh:
    columns = json.load(fh)


with open(os.path.join('pipeline.pickle'), 'rb') as fh:
    pipeline = joblib.load(fh)


with open(os.path.join('dtypes.pickle'), 'rb') as fh:
    dtypes = pickle.load(fh)


# End model un-pickling
########################################

########################################
# Input validation functions



# End input validation functions
########################################

########################################
# Begin webserver stuff

def b(obs_dict):
    if "observation_id" not in obs_dict:
        base_request["observation_id"] = None
        base_request["error"] = "Field `id` missing from request: {}".format(obs_dict)
        
        
        return obs_dict
    return obs_dict


app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict(): 
    obs_dict = request.get_json()
    
    #obs_dict = b(obs_dict)
    #_id = obs_dict['observation_id']
    
    try:
        _id = obs_dict["observation_id"]
    except:
        _id = None
        return ({"observation_id": _id,
                "error": "observation_id is missinggg"})
    
    try:
        observation = obs_dict['data']
    except KeyError:
        response = {}
        response["error"] = "data is missing: {}".format(obs_dict)
         #print(response)
        return response  
     
     #ourlist = ['age','workclass','sex','race','education','marital-status','capital-gain','capital-loss','hours-per-week']
     #for a in ourlist:
     #    if a not in list(request['data'].keys()):
      #       response = {}
      #       response["error"] = "Field `id` missing from request: {}".format(base_request)
      #       return response
        # checking for missing columns
    request_columns = list(obs_dict['data'].keys())
    
    for column in columns:
        if column not in request_columns:
            return {"observation_id": _id,
                    "error": "{0} is missing".format(column)}
    # checking for extra columns
    for column in request_columns:
        if column not in columns:
            return {"observation_id": _id,
                    "error": "{0} is an extra column".format(column)}
    #for a in list(obs_dict['data'].keys()):
    #    if a not in list(base_request['data'].keys()):
     #       response = {}
     #       response["error"] = "Field `id` missing from request: {}".format(obs_dict)
      #      return response 

    if obs_dict['data']['sex'] not in ["Male", "Female"]:
        return {"error": "{0} is not a valid option for sex".format(obs_dict['data']['sex'])}

    if obs_dict['data']['race'] not in ['White', 'Black', 'Asian-Pac-Islander', 'Amer-Indian-Eskimo',
        'Other']:
        return {"error": "{0} is not a valid option for race".format(obs_dict['data']['race'])}

    if obs_dict['data']['age'] <= 0 or obs_dict['data']['age'] >100:
        return {"error": "{0} is not a valid option for age".format(obs_dict['data']['age'])}

    if obs_dict['data']['capital-gain'] < 0:
        return {"error": "{0} is not a valid option for capital-gain".format(obs_dict['data']['capital-gain'])}

    if obs_dict['data']['capital-loss'] < 0:
        return {"error": "{0} is not a valid option for capital-loss".format(obs_dict['data']['capital-loss'])}

    if obs_dict['data']['hours-per-week'] <= 0 or obs_dict['data']['hours-per-week'] >100:
        return {"error": "{0} is not a valid option for hours-per-week".format(obs_dict['data']['hours-per-week'])}

    obs = pd.DataFrame([observation], columns=columns)
    obs = obs.astype(dtypes)
    proba = pipeline.predict_proba(obs)[0, 1]
    prediction = pipeline.predict(obs)[0]
    response_pp = {'prediction': bool(prediction), 'proba': proba}

    if "error" in obs_dict:
        response =  {  
        "observation_id":_id,
        "prediction": response_pp['prediction'],
        "probability": response_pp['proba'],
        "error":request['error']
        }
    else:
        response =  {  
        "observation_id":_id,
        "prediction": response_pp['prediction'],
        "probability": response_pp['proba']}
     
    return jsonify(response)
    
@app.route('/update', methods=['POST'])
def update():
    obs = obs_dict.get_json()
    try:
        p = Prediction.get(Prediction.observation_id == obs['id'])
        p.true_class = obs['true_class']
        p.save()
        return jsonify(model_to_dict(p))
    except Prediction.DoesNotExist:
        error_msg = 'Observation ID: "{}" does not exist'.format(obs['id'])
        return jsonify({'error': error_msg})

    
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)