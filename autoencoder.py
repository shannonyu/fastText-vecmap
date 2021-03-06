# -*- coding: utf-8 -*-
"""autoencoder.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1eEw3YSM-XGLjUhrkrWKYQGxDAXaqlJdj
"""

import tensorflow as tf
import pandas as pd
import numpy as np
from google.colab import files

__author__ = "Olivares José"

print("TensorFlow",tf.VERSION)
if tf.test.gpu_device_name():
  print("GPU disponible")

import sys
print(sys.version)

LOG_DIR = '/tmp/model1'
get_ipython().system_raw(
    'tensorboard --logdir {} --host 0.0.0.0 --port 6006 &'
    .format(LOG_DIR)
)

! curl http://localhost:6006

! wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip > /dev/null 2>&1
! unzip ngrok-stable-linux-amd64.zip > /dev/null 2>&1

get_ipython().system_raw('./ngrok http 6006 &')

! curl -s http://localhost:4040/api/tunnels | python3 -c \
    "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"

# Install
! npm install -g localtunnel

# Tunnel port 6006 (TensorBoard assumed running)
get_ipython().system_raw('lt --port 6006 >> url.txt 2>&1 &')

# Get url
! cat url.txt

"""
# Cargar archivos necesarios
## Lexicon de entrenamiento

# Vectores N2V/W2V
"""

# Cargar vectores objetivo
target_embeddings = files.upload()

# Cargar vectores fuente
source_embeddings = files.upload()

# Convertir archivos de entrenamiento a una lista
source_embeddings = source_embeddings['es.496.128d.train.n2v'].decode("utf-8").split("\n")
target_embeddings = target_embeddings['na.496.128d.train.n2v'].decode("utf-8").split("\n")

def create_vectors_dataframe(df):
  # Separar cada elemento de la lista en una tupla
  df_tmp = list()
  for i in df:
      if i == 0:
          pass
      else:
          df_tmp.append(tuple(i.split()))

  # Eliminar el primer elemento, no se utiliza
  #df_tmp.pop(0)
  return pd.DataFrame.from_records(df_tmp)

# Crear dataframes con los vectores train
source_df = create_vectors_dataframe(source_embeddings)
target_df = create_vectors_dataframe(target_embeddings)

source_df.head()

target_df.head()

source_df.shape,target_df.shape

"""# Los dataframes solo contienen los vectores de entrenamiento, ya no es necesario buscarlo por índices"""

target_dummy = target_df.drop(target_df.columns[0], axis=1)
target_vectores = target_dummy.values.astype(np.float64)
source_dummy = source_df.drop(source_df.columns[0], axis=1)
source_vectores = source_dummy.values.astype(np.float64)

source_vectores.shape,target_vectores.shape

"""# Duplicar datos de entrenamiento"""

es_dummy = source_vectores
na_dummy = target_vectores
for i in range(es_dummy.shape[0]):
    source_vectores=np.vstack((source_vectores,es_dummy[i][::-1]))
    target_vectores=np.vstack((target_vectores,na_dummy[i][::-1]))

source_vectores.shape,target_vectores.shape

def next_batch(x,y, step, batch_size):
    """Función para obtener batches de un conjunto de datos
    
    Arguments:
        x {numpyarray} -- Conjunto de datos (inputs).
        y {numpyarray} -- Conjunto de datos (targets).
        step {int} -- Batches.
        batch_size {int} -- Tamaño del batch.
    
    Returns:
        numpyarray -- Subconjunto de tamaño batch_size.
    """

    return x[batch_size * step:batch_size * step + batch_size],y[batch_size * step:batch_size * step + batch_size]

class AE(tf.keras.Model):
  def __init__(self,NODES_H1,NODES_OUT,k):
    super(AE, self).__init__()
    self.dense1=tf.keras.layers.Dense(NODES_H1, activation=tf.nn.elu)
    self.dense2=tf.keras.layers.Dense(NODES_OUT,activation=tf.nn.tanh)
    self.dropout=tf.keras.layers.Dropout(rate=k,seed=42)
    
  def call(self,inputs,training=False):
    x = self.dense1(inputs)
    if training:
      x=self.dropout(x,training=training)
    return self.dense2(x)

#https://ikhlestov.github.io/posts/rbm-based-autoencoders-with-tensorflow/
#https://gist.github.com/blackecho/db85fab069bd2d6fb3e7

# Entrenamiento

%%time
import datetime
print(datetime.datetime.now())
tf.reset_default_graph()
tf.set_random_seed(42)
print("TensorFlow v{}".format(tf.__version__))
print(tf.test.gpu_device_name())

LEARNING_RATE = 0.001
EPOCHS = 600#1000h1-370
# Dimensión de vectores de entrada (número de neuronas en capa de entrada).
NODES_INPUT = source_vectores.shape[1]

# Número de neuronas en capas ocultas.
NODES_H1 = 300   #70 - 20 - 15
NODES_H2 = 220  # 42 - 20
NODES_H3 = 180  # 42 - 20
NODES_H4 = 50  # 42 - 20
NODES_H5 = 950

# Dimensión de vectores de salida (número de neuronas en capa de salida).
NODES_OUTPUT = target_vectores.shape[1]

DROPOUT = 0.51

model = "model2250"


with tf.name_scope('input'):
    X = tf.placeholder(shape=[None, NODES_INPUT],dtype=tf.float64, name='input_es')
    y = tf.placeholder(shape=[None, NODES_OUTPUT],dtype=tf.float64, name='target_na')


kprob = tf.placeholder(tf.float64,name='dropout_prob')


# Se definen las capas.


dense1 = tf.layers.dense(inputs=X,
                        units=NODES_H1,
                        activation=tf.nn.elu,
                        use_bias=True,
                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.1,seed=42),
                        name="h1")
dense1=tf.layers.dropout(dense1,rate=DROPOUT,seed=42)

'''
dense2 = tf.layers.dense(inputs=dense1,
                        units=NODES_H2,
                        activation=tf.nn.tanh,
                        use_bias=True,
                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.1,seed=42),
                        name="h2")
dense2=tf.layers.dropout(dense2,rate=DROPOUT,seed=42)

dense3 = tf.layers.dense(inputs=dense2,
                        units=NODES_H1,
                        activation=tf.nn.tanh,
                        use_bias=True,
                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.1,seed=42),
                        name="h3")
dense3=tf.layers.dropout(dense3,rate=DROPOUT,seed=42)

dense4 = tf.layers.dense(inputs=dense3,
                        units=NODES_H1,
                        activation=tf.nn.tanh,
                        use_bias=True,
                        kernel_initializer=tf.truncated_normal_initializer(stddev=0.1,seed=42),
                        name="h4")
dense4=tf.layers.dropout(dense4,rate=DROPOUT,seed=42)
'''
nah_predicted = tf.layers.dense(inputs=dense1,
                               units=NODES_OUTPUT,
                               activation=tf.nn.tanh,
                               use_bias=True,
                               kernel_initializer=tf.truncated_normal_initializer(stddev=0.1,seed=42),
                               name="nah_predicted")

# Función de error
loss = tf.reduce_mean(tf.squared_difference(nah_predicted, y), name="loss")


tf.summary.scalar("loss", loss)


# backprop
optimiser = tf.train.RMSPropOptimizer(learning_rate=LEARNING_RATE,centered=True)


# Compute gradients
gradients, variables = zip(*optimiser.compute_gradients(loss))

gradients, _ = tf.clip_by_global_norm(gradients, 5.0)

# Apply processed gradients to optimizer.
train_op = optimiser.apply_gradients(zip(gradients, variables))


# Accuracy 
with tf.name_scope('accuracy'):
    with tf.name_scope('correct_prediction'):
        # Se compara salida de la red neuronal con el vector objetivo.
        correct_prediction = tf.equal(tf.argmax(nah_predicted, 1), tf.argmax(y, 1))
    with tf.name_scope('accuracy'):
        # Se calcula la precisión.
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float64))
    tf.summary.scalar('accuracy', accuracy)


LOGPATH = "logs/model"
print("logpath:", LOGPATH)


# Se crea la sesión
config = tf.ConfigProto(log_device_placement=True)
sess =  tf.Session(config=config)

# Se ponen los histogramas y valores de las gráficas en una sola variable.
summaryMerged = tf.summary.merge_all()

# Escribir a disco el grafo generado y las gráficas para visualizar en TensorBoard.
writer = tf.summary.FileWriter(LOGPATH, sess.graph)

# Se inicializan los valores de los tensores.
init = tf.global_variables_initializer()

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

# Ejecutando sesión
sess.run(init)


for j in range(EPOCHS):
    
    #for i in range(0,10):
      #source_batch, target_batch = next_batch(source_vectores,target_vectores, i, 500)
    _loss, _, sumOut = sess.run([loss, train_op, summaryMerged],
                                feed_dict={X: source_vectores, y: target_vectores, kprob:DROPOUT})
      

    writer.add_summary(sumOut, j)
    
    if ((j % 150) == 0) or (j == EPOCHS-1):
      #train_accuracy = accuracy.eval(session=sess, feed_dict={X: tsource_vectores, y: ttarget_vectores,kprob:1})
      print("Epoch:", j, "/", EPOCHS, "\tLoss:",_loss)#,"\tAccuracy:", train_accuracy)
        

        

SAVE_PATH = "./"+model+".ckpt"
print("save path",SAVE_PATH)
save_model = saver.save(sess, SAVE_PATH)
print("Model saved in file: %s", SAVE_PATH)
writer.close()

# Descargar modelo generado
"""

files.download("/content/checkpoint")

files.download("/content/"+model+".ckpt.meta")

files.download("/content/"+model+".ckpt.index")

files.download("/content/"+model+".ckpt.data-00000-of-00001")

! ls -la logs/model

files.download("/content/logs/model/events.out.tfevents.1530060264.6d9669b54958")

