from pspnet import *
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import tensorflow as tf
import rospy
import os
import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2

'''
Real time image segmentation, using PSPNet101. Dummy publisher which is Really Really Slow.
'''

class Semantic_Imformation_Publisher():
    def __init__(self):
        self._cv_bridge = CvBridge()
        self._session = tf.Session()
        self.pspnet = PSPNet101(nb_classes=19, input_shape=(713, 713),
                                       weights='pspnet101_cityscapes')
        init = tf.global_variables_initializer()
        self._session.run(init)
        self._sub = rospy.Subscriber('image', Image, self.callback, queue_size = 1)
        self._pub = rospy.Publisher('result', Image, queue_size = 1)
    
    def callback(self, image_msg):
        cv_image = self._cv_bridge.imgmsg_to_cv2(image_msg, "bgr8")
        h_ori, w_ori = cv_image.shape[:2]
        #rospy.loginfo(self._pspnet.model.summary())
        tensor = self._session.graph.get_tensor_by_name('activation_109/truediv:0')
        probs = self._session.run(tensor, {'input_1:0':self.img_proc(cv_image)})[0]
        if cv_image.shape[0:1] != (713,713):  # upscale prediction if necessary
            h, w = probs.shape[:2]
            probs = ndimage.zoom(probs, (1. * h_ori / h, 1. * w_ori / w, 1.),
                                 order=1, prefilter=False)
        #probs = self.pspnet.predict(cv_image)
        rospy.loginfo("running")
        cm = np.argmax(probs, axis=2)
        pm = np.max(probs, axis=2)
        color_cm = utils.add_color(cm)
        alpha_blended = 0.5 * color_cm * 255 + 0.5 * cv_image
        alpha_blended = self._cv_bridge.cv2_to_imgmsg(alpha_blended)
        self._pub.publish(alpha_blended)
    

    def img_proc(self, img):
        # Preprocess
        img = misc.imresize(img, (713,713))
        img = img - DATA_MEAN
        img = img[:, :, ::-1]  # RGB => BGR
        img = img.astype('float32')
        data = np.expand_dims(img, 0)
        return data

    def main(self):
        rospy.spin()

if __name__ == '__main__':
    rospy.init_node('Semantic_Information_Publisher')
    tensor = Semantic_Imformation_Publisher()
    tensor.main()
