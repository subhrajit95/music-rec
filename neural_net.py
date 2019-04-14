#!/usr/bin/env python3
# coding: utf-8
"""
neural_net.py
04-03-19
jack skrable
"""

import time
import datetime
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from keras import optimizers 
from keras import regularizers
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.callbacks import TensorBoard
from keras.utils import to_categorical
from keras import backend as K

def simple_nn(X, y, label):

    K.clear_session()

    # Globals
    lr = 0.001
    epochs = 200
    batch_size = 64
    OPT = 'adamax'

    t = time.time()
    dt = datetime.datetime.fromtimestamp(t).strftime('%Y%m%d%H%M%S')
    name = '_'.join([OPT, str(epochs), str(batch_size), dt]) + '.json'

    # Calculate class weights to improve accuracy 
    class_weights = dict(enumerate(compute_class_weight('balanced', np.unique(y), y)))
    swm = np.array([class_weights[i] for i in y])

    # Convert target to categorical
    y = to_categorical(y, num_classes=y.shape[0])

    # Split up input to train/test/validation
    print('Splitting to train, test, and validation sets...')
    X_train, X_test, X_valid = np.split(X, [int(.6 * len(X)), int(.8 * len(X))])
    y_train, y_test, y_valid = np.split(y, [int(.6 * len(y)), int(.8 * len(y))])

    # Get input and output layer sizes from input data
    in_size = X_train.shape[1]
    # Modify this when increasing artist list target
    out_size = y.shape[0]

    # Initialize the constructor
    model = Sequential()

    # Add an input layer 
    model.add(Dense(12, activation='relu', input_shape=(in_size,)))

    # Add hidden layers
    model.add(Dense(in_size // 2,
                    activation='relu',
                    # Regularize to reduce overfitting
                    activity_regularizer=regularizers.l1(1e-08),
                    kernel_regularizer=regularizers.l1(1e-06)))
    # Dropout to reduce overfitting
    model.add(Dropout(0.1))
    model.add(Dense(in_size // 4,
                    activation='relu',
                    kernel_regularizer=regularizers.l1(1e-06)))
    model.add(Dropout(0.1))
    model.add(Dense(in_size // 10,
                    activation='relu',
                    kernel_regularizer=regularizers.l1(1e-06)))

    # Add an output layer 
    model.add(Dense(out_size, activation='softmax'))

    if OPT == 'sgd':
        opt = optimizers.SGD(lr=lr, decay=1e-6, momentum=0.8, 
                             nesterov=True)
    elif OPT == 'adam':
        opt = optimizers.Adam(lr=lr, beta_1=0.9, beta_2=0.999,
                              epsilon=None, decay=1e-6, amsgrad=False)
    elif OPT == 'adamax':
        opt = optimizers.Adamax(lr=lr, beta_1=0.9, beta_2=0.999,
                                epsilon=None, decay=0.0)

    # def metric_categorical_crossentropy(y_true, y_pred):
    #     return

    model.compile(loss='categorical_crossentropy',
                  optimizer=opt,
                  metrics=['accuracy','msle'],
                  sample_weight_mode=swm)



    tensorboard = TensorBoard(log_dir=str('./logs/'+label+'/'+name),
                              histogram_freq=1,
                              write_graph=True,
                              write_images=False)  

    # tensorboard = TensorBoard(log_dir=str('./logs/'+label+'/'+name))                     

    print('Training...')    
    # model.fit(tf.convert_to_tensor(X_train), tf.convert_to_tensor(y_train), validation_data=(X_valid, y_valid), epochs=epochs, steps_per_epoch=batch_size, validation_steps=25, verbose=1, shuffle=True, callbacks=[tensorboard])
    model.fit(X, y, validation_data=(X_valid, y_valid), epochs=epochs, batch_size=batch_size, verbose=1, shuffle=True, callbacks=[tensorboard])

    print('EValuating...')
    y_pred = model.predict(X_test)

    score = model.evaluate(X_test, y_test,verbose=1)

    print(score)

    print('Saving model...')

    path = './model/train/' + label + '/'
    model.save(str(path+name+'.h5'))

    return model

def deep_nn(X,y):

    print('Splitting to train, test, and validation sets...')
    # y = keras.utils.to_categorical(y, num_classes=y.shape[0])
    X_train, X_test, X_valid = np.split(X, [int(.6 * len(X)), int(.8 * len(X))])
    y_train, y_test, y_valid = np.split(y, [int(.6 * len(y)), int(.8 * len(y))])
    in_size = X_train.shape[1]
    out_size = y.shape[0]

    def shuffle_batch(X, y, batch_size):
        rnd_idx = np.random.permutation(len(X))
        n_batches = np.ceil(len(X) / batch_size).astype(int)
        for batch_idx in np.array_split(rnd_idx, n_batches):
            X_batch, y_batch = X[batch_idx], y[batch_idx]
            yield X_batch, y_batch

    n_inputs = in_size 
    n_hidden1 = in_size // 4
    n_hidden2 = in_size // 8
    n_hidden3 = 100
    n_outputs = out_size

    learning_rate = 0.001

    n_epochs = 100
    batch_size = 200

    X = tf.placeholder(tf.float32, shape=(None, n_inputs), name="X")
    y = tf.placeholder(tf.int32, shape=(None), name="y")

    with tf.name_scope("dnn"):
        hidden_layer_1 = tf.layers.dense(X, n_hidden1, activation=tf.nn.relu, name="hidden_layer_1")
        hidden_layer_2 = tf.layers.dense(hidden_layer_1, n_hidden2, activation=tf.nn.relu, name="hidden_layer_2")
        hidden_layer_3 = tf.layers.dense(hidden_layer_2, n_hidden3, activation=tf.nn.relu, name="hidden_layer_3")
        logits = tf.layers.dense(hidden_layer_3, n_outputs, name="outputs")

        tf.summary.histogram('hidden_layer_1', hidden_layer_1)
        tf.summary.histogram('hidden_layer_2', hidden_layer_2)
        tf.summary.histogram('hidden_layer_3', hidden_layer_3)

    with tf.name_scope("loss"):
        xentropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y, logits=logits)
        loss = tf.reduce_mean(xentropy, name="loss")

    with tf.name_scope("train"):
        optimizer = tf.train.GradientDescentOptimizer(learning_rate)
        training_op = optimizer.minimize(loss)

    with tf.name_scope("eval"):
        correct = tf.nn.in_top_k(logits, y, 1)
        accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))
        tf.summary.scalar('accuracy', accuracy)

    init = tf.global_variables_initializer()
    merged_summaries = tf.summary.merge_all()

    saver = tf.train.Saver()

    means = X_train.mean(axis=0, keepdims=True)
    stds = X_train.std(axis=0, keepdims=True) + 1e-10
    X_val_scaled = (X_valid - means) / stds

    train_saver = tf.summary.FileWriter('./model/train', tf.get_default_graph())  # async file saving object
    test_saver = tf.summary.FileWriter('./model/test')  # async file saving object

    with tf.Session() as sess:
        init.run()
        for epoch in range(n_epochs):
            for X_batch, y_batch in shuffle_batch(X_train, y_train, batch_size):
                X_batch_scaled = (X_batch - means) / stds
                summaries, _ = sess.run([merged_summaries, training_op], feed_dict={X: X_batch, y: y_batch})
            train_saver.add_summary(summaries, epoch)
            _, acc_batch = sess.run([merged_summaries, accuracy], feed_dict={X: X_batch, y: y_batch})
            train_summaries, acc_valid = sess.run([merged_summaries, accuracy], feed_dict={X: X_valid, y: y_valid})
            test_saver.add_summary(train_summaries, epoch)
            print(epoch, "Batch accuracy:", acc_batch, "Validation accuracy:", acc_valid)

        train_saver.flush()
