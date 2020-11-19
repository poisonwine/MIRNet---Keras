import os
import math
import argparse
import numpy as np
import tensorflow as tf

from model import MIRNet
from tensorflow import keras
from IPython.display import display
from tensorflow.keras import Input, Model

from utils import *

train_ds = SSID(subset='train').dataset(repeat_count=1)
valid_ds = SSID(subset='valid').dataset(repeat_count=1)

test_path = 'test/denoise'
test_img_paths = sorted(
    [
        os.path.join(test_path, fname)
        for fname in os.listdir(test_path)
        if fname.endswith(".png")
    ]
)

def train(config):
    os.environ['CUDA_VISIBLE_DEVICES'] = config.gpu

    mir_x = MIRNet(64, config.num_mrb, config.num_rrg)
    x = Input(shape=(None, None, 3))
    out = mir_x.main_model(x)
    model = Model(inputs=x, outputs=out)
    model.summary()

    early_stopping_callback = keras.callbacks.EarlyStopping(monitor="loss", patience=10)
    checkpoint_filepath = config.checkpoint_filepath

    model_checkpoint_callback = keras.callbacks.ModelCheckpoint(
        checkpoint_filepath + '/best.h5',
        monitor="loss",
        mode="min",
        save_best_only=True,
        period=config.checkpoint_ep
    )

    callbacks = [ESPCNCallback(test_img_paths), early_stopping_callback, model_checkpoint_callback]
    loss_fn = keras.losses.MeanSquaredError()
    optimizer = keras.optimizers.Adam(learning_rate = config.lr)

    epochs = config.num_epochs

    model.compile(
        optimizer=optimizer, loss=loss_fn,
    )

    model.fit(
        train_ds, epochs=epochs, callbacks=callbacks, validation_data=valid_ds, verbose=1
    )


if __name__ == "__main__":
    
	parser = argparse.ArgumentParser()

	# Input Parameters
	parser.add_argument('--lr', type=float, default=1e-4)
	parser.add_argument('--gpu', type=int, default=0)
	parser.add_argument('--grad_clip_norm', type=float, default=0.1)
	parser.add_argument('--num_epochs', type=int, default=100)
	parser.add_argument('--train_batch_size', type=int, default=32)
	parser.add_argument('--checkpoint_ep', type=int, default=1)
	parser.add_argument('--checkpoint_filepath', type=str, default="weights/denoise/")
	parser.add_argument('--num_rrg', type=int, default= 3)
	parser.add_argument('--num_mrb', type=int, default= 2)

	config = parser.parse_args()

	if not os.path.exists(config.checkpoints_folder):
		os.mkdir(config.checkpoints_folder)

	train(config)