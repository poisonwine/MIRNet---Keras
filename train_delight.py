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

train_ds = LOL(subset='train').dataset(repeat_count=1)
valid_ds = LOL(subset='valid').dataset(repeat_count=1)

test_path = 'test/delight/'
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

    early_stopping_callback = keras.callbacks.EarlyStopping(monitor="val_psnr_delight", patience=10, mode='max')
    checkpoint_filepath = config.checkpoint_filepath
    reduce_lr_loss = keras.callbacks.ReduceLROnPlateau(monitor='val_psnr_delight', factor=0.5, patience=5, verbose=1, epsilon=1e-7, mode='max')

    
    model_checkpoint_callback = keras.callbacks.ModelCheckpoint(
        checkpoint_filepath + f'{{epoch:02d}}_{{val_psnr_delight:.2f}}.h5',
        monitor="val_psnr_delight",
        mode="max",
        save_best_only=True,
        period=1
    )

    callbacks = [ESPCNCallback(test_img_paths, mode=config.mode, checkpoint_ep=config.checkpoint_ep), early_stopping_callback, model_checkpoint_callback, reduce_lr_loss]
    loss_fn = keras.losses.MeanAbsoluteError()
    optimizer = keras.optimizers.Adam(learning_rate = config.lr)

    epochs = config.num_epochs

    model.compile(
        optimizer=optimizer, loss=loss_fn, metrics=[psnr_delight]
    )

    model.fit(
        train_ds, epochs=epochs, callbacks=callbacks, validation_data=valid_ds, verbose=1
    )


if __name__ == "__main__":
    
	parser = argparse.ArgumentParser()

	# Input Parameters
	parser.add_argument('--lr', type=float, default=1e-4)
	parser.add_argument('--gpu', type=str, default='0')
	parser.add_argument('--grad_clip_norm', type=float, default=0.1)
	parser.add_argument('--num_epochs', type=int, default=100)
	parser.add_argument('--train_batch_size', type=int, default=32)
	parser.add_argument('--checkpoint_ep', type=int, default=10)
	parser.add_argument('--checkpoint_filepath', type=str, default="weights/delight/")
	parser.add_argument('--num_rrg', type=int, default= 3)
	parser.add_argument('--num_mrb', type=int, default= 2)
	parser.add_argument('--mode', type=str, default= 'delight')

	config = parser.parse_args()

	if not os.path.exists(config.checkpoint_filepath):
		os.mkdir(config.checkpoint_filepath)

	train(config)