#!/usr/bin/env python3
# coding: utf-8
"""
api.py
04-14-19
jack skrable
"""

import os
import json
import tensorflow as tf
import numpy as np
import pandas as pd
import flask

# custom module imports
# import predict
import neural_net as nn
import read_h5 as read
import preprocessing as pp

# initialize our Flask application and the Keras model
app = flask.Flask(__name__)
model = None
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.logging.set_verbosity(tf.logging.ERROR)

def load_lookups():
	global lookupDF
	global song_file_map
	global column_maps
	global max_list

	lookupDF = pd.read_hdf('./frontend/data/lookup.h5', 'df')
	with open('./data/song-file-map.json', 'r') as f:
		song_file_map = json.load(f)
	with open('./model/working/preprocessing/maps.json', 'r') as f:
		column_maps = json.load(f)
	with open('./model/working/preprocessing/max_list.json', 'r') as f:
		max_list = json.load(f)


def process_metadata_list(col):
    x_map = column_maps[col.name]
    max_len = max_list[col.name]
    col = col.apply(lambda x: pp.lookup_discrete_id(x, x_map))
    col = col.apply(lambda x: np.pad(x, (0, max_len - x.shape[0]), 'constant'))
    xx = np.stack(col.values)
    return xx


def preprocess_predictions(df):
    print('Vectorizing dataframe...')
    output = np.zeros(shape=(len(df),1))

    for col in df:
        print('Vectorizing ',col)
        if df[col].dtype == 'O':
            if type(df[col].iloc[0]) is str:
                xx = pp.lookup_discrete_id(df[col], column_maps[col])
                xx = xx.reshape(-1,1)
            elif col.split('_')[0] == 'metadf':
                xx = process_metadata_list(df[col])
            else:
                xx = pp.process_audio(df[col])

        else:
            xx = df[col].values[...,None]

        # Normalize each column    
        xx = xx / (np.linalg.norm(xx) + 0.00000000000001)
        print(xx)
        print(output)
        output = np.hstack((output, xx))

    return output


@app.route("/recommend", methods=["GET"])
def recommend():
	# initialize the data dictionary that will be returned from the
	# view
	data = {"success": False}

	# GET requests
	if flask.request.method == "GET":
		
		# Separate this into a new module for prediction preprocssing
		# Snag query string of song IDs
		song_ids = flask.request.args.get('songs')
		song_ids = song_ids.split(',')
		# Lookup filenames by song id
		files = [song_file_map[id] for id in song_ids]
		# Extract raw data from files
		df = read.extract_song_data(files)
		df = pp.convert_byte_data(df)
		# Vectorize
		X = preprocess_predictions(df)
		# df = pp.create_target_classes(df)

		print(df)

		# indicate that the request was a success
		data["success"] = True

	# JSONify data for response
	response = flask.jsonify(data)
	# Allow CORS
	response.headers.add('Access-Control-Allow-Origin', '*')

	return response


@app.route("/lookup", methods=["GET"])
def lookup():
	# initialize the data dictionary that will be returned from the
	# view
	data = {"success": False}

	# ensure an image was properly uploaded to our endpoint
	if flask.request.method == "GET":
		
		# Get lookup data here		
		data['entity'] = lookupDF.to_dict('records')

		# indicate that the request was a success
		data["success"] = True

	# JSONify data for response
	response = flask.jsonify(data)
	# Allow CORS
	response.headers.add('Access-Control-Allow-Origin', '*')

	return response

# if this is the main thread of execution first load the model and
# then start the server
if __name__ == "__main__":
	print(" * Starting Flask server and loading Keras model...")
	print(" * Please wait until server has fully started")

	# Load my model 
	model = nn.load_model('./model/working/std')
	# Get songs for lookup function
	load_lookups()

	print(' * Server is active')
	# Run app
	app.run(host='0.0.0.0', port=5001)
