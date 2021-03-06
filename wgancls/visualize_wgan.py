from model import WGanCls
from utils import save_images, get_balanced_factorization, make_gif
from saver import load
from visualize import *
from ops import NHWC
from dataset import TextDataset
import tensorflow as tf
import numpy as np


class WGanClsVisualizer(object):
    def __init__(self, sess: tf.Session, model: WGanCls, dataset: TextDataset, config):
        self.sess = sess
        self.model = model
        self.dataset = dataset
        self.config = config
        self.samples_dir = self.config['SAMPLE_DIR']

    def visualize(self):
        z = tf.placeholder(tf.float32, [self.model.batch_size, self.model.z_dim], name='z')
        phi = tf.placeholder(tf.float32, [self.model.batch_size] + [self.model.embed_dim], name='cond')
        gen, _, _ = self.model.generator(z, phi, is_training=False)
        gen_no_noise, _, _ = self.model.generator(z, phi, reuse=True, is_training=False, cond_noise=False)

        saver = tf.train.Saver(tf.global_variables('g_net'))
        could_load, _ = load(saver, self.sess, self.config['CHECKPOINT_DIR'])
        if could_load:
            print(" [*] Load SUCCESS")
        else:
            print(" [!] Load failed...")
            raise RuntimeError('Could not load the checkpoints of the generator')

        dataset_pos = np.random.randint(0, self.dataset.test.num_examples)
        for idx in range(10):
            dataset_pos = np.random.randint(0, self.dataset.test.num_examples)

            # Interpolation in z space:
            # ---------------------------------------------------------------------------------------------------------
            _, cond, _, captions = self.dataset.test.next_batch_test(1, dataset_pos, 1)
            cond = np.squeeze(cond, axis=0)
            caption = captions[0][0]

            samples = gen_noise_interp_img(self.sess, gen_no_noise, cond, self.model.z_dim, self.model.batch_size)
            save_cap_batch(samples, caption, '{}/{}_visual/z_interp/z_interp{}.png'.format(self.samples_dir,
                                                                                           self.dataset.name,
                                                                                           idx))
            # Interpolation in embedding space:
            # ---------------------------------------------------------------------------------------------------------
            _, cond, _, caps = self.dataset.test.next_batch_test(2, dataset_pos, 1)
            cond = np.squeeze(cond, axis=0)
            cond1, cond2 = cond[0], cond[1]
            cap1, cap2 = caps[0][0], caps[1][0]

            samples = gen_cond_interp_img(self.sess, gen_no_noise, cond1, cond2, self.model.z_dim,
                                          self.model.batch_size)
            save_interp_cap_batch(samples, cap1, cap2,
                                  '{}/{}_visual/cond_interp/cond_interp{}.png'.format(self.samples_dir,
                                                                                      self.dataset.name,
                                                                                      idx))
            # make_gif(samples, '{}/{}_visual/cond_interp/gifs/cond_interp{}.gif'.format(self.samples_dir,
            #                                                                            self.dataset.name,
            #                                                                            idx), duration=4)

            # Generate captioned image
            # ---------------------------------------------------------------------------------------------------------
            _, conditions, _, captions = self.dataset.test.next_batch_test(1, dataset_pos, 1)
            conditions = np.squeeze(conditions, axis=0)
            caption = captions[0][0]
            samples = gen_captioned_img(self.sess, gen, conditions, self.model.z_dim, self.model.batch_size)

            save_cap_batch(samples, caption, '{}/{}_visual/cap/cap{}.png'.format(self.samples_dir,
                                                                                 self.dataset.name, idx))
        for idx, special_pos in enumerate([1126, 908, 398,129,267, 425, 587, 631, 756, 801, 1001]):
            print(special_pos)
            # Generate specific image
            # ---------------------------------------------------------------------------------------------------------
            _, conditions, _, captions = self.dataset.test.next_batch_test(1, special_pos, 1)
            conditions = np.squeeze(conditions, axis=0)
            caption = captions[0][0]
            samples = gen_captioned_img(self.sess, gen, conditions, self.model.z_dim, self.model.batch_size)

            save_cap_batch(samples, caption, '{}/{}_visual/special_cap/cap{}.png'.format(self.samples_dir,
                                                                                         self.dataset.name, idx))

        # Generate some images and their closest neighbours
        # ---------------------------------------------------------------------------------------------------------
        _, conditions, _, _ = self.dataset.test.next_batch_test(self.model.batch_size, dataset_pos, 1)
        conditions = np.squeeze(conditions)
        samples, neighbours = gen_closest_neighbour_img(self.sess, gen, conditions, self.model.z_dim,
                                                        self.model.batch_size, self.dataset)
        batch = np.concatenate([samples, neighbours])
        text = 'Generated images and their closest neighbours'
        save_cap_batch(batch, text, '{}/{}_visual/neighb/neighb.png'.format(self.samples_dir,
                                                                            self.dataset.name))




