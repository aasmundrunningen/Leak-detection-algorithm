import time
import sys
sys.path.append(r'/home/pi/picar-x/lib')
from utils import reset_mcu
reset_mcu()
import time

from picamera import PiCamera

from grayscale_module import Grayscale_Module

from ultrasonic import Ultrasonic
from pin import Pin

from picarx import Picarx
px = Picarx()

from tts import TTS
tts = TTS()

import cv2
import numpy as np
from PIL import Image
import io
from tqdm import tqdm
import os

from PIL import Image
from pyzbar.pyzbar import decode


def outputs(num, delay, index):
    stream = io.BytesIO()
    print("Taking pictures")
    for i in tqdm(range(num)):
        yield stream
        stream.seek(0)
        img = Image.open(stream).save(f"/home/pi/Pictures/Image_{i}.jpeg")
        if i == 0:
            Image.open(stream).save(f"/home/pi/Image_0_{index}.jpeg")
        stream.seek(0)
        stream.truncate()
        time.sleep(delay)


def create_image(data, name):
    array1 = np.array(data, dtype=np.uint8)
    Image.fromarray(array1).save(f"/home/pi/Pictures/{name}.jpeg")

def findAverage(index):
    filenames = os.listdir(r"/home/pi/Pictures")
    images = []
    print("converting to arrays")
    for filename in tqdm(filenames):
        img = cv2.imread(f"/home/pi/Pictures/{filename}", 0)
        images += [np.array(img, dtype=np.uint8)]


    print("calculating average")
    size = np.shape(images[0])
    avgIm = np.zeros((size))
    for image in tqdm(images):
        avgIm = np.add(image, avgIm)
    avgIm = np.multiply(avgIm, 1/len(images))
    
    print("calculating error")
    errorIm = np.zeros((size))
    for image in tqdm(images):
        diff = np.absolute(np.subtract(image, avgIm))
        errorIm = np.add(errorIm, diff)
    errorIm = errorIm.astype(int)
    errorIm[errorIm < 60] = 0
    img = Image.fromarray(errorIm).convert("RGB")
    img.save('error_img.jpeg')

    # Smoothes picture
    img = cv2.imread("/home/pi/error_img.jpeg",0)
    blur = cv2.GaussianBlur(img,(13,13),0)
    thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)[1]
    
    try:
        # Box
        mask=Image.fromarray(thresh)
        box = mask.getbbox()
        print(box)
        img = Image.fromarray(thresh).convert("RGB")
        img.save(f'error_img_{index}.jpeg')
        img = cv2.imread("/home/pi/Pictures/Image_0.jpeg")
        img = cv2.rectangle(img, (box[0] - 20,box[1] - 20), (box[2] + 20, box[3]+ 20), (0,255,0), 1)
        img = Image.fromarray(img).save(f"Image_detected_{index}.jpeg")
        return True
    except TypeError:
        return False

    

    # box = cv2.minAreaRect(np.array([thresh], dtype=np.int32))
    # print(box)

def check(num, index):
    try:
        with PiCamera() as camera:
            delay = 0
            camera.resolution = (640, 480)
            camera.framerate = 20
            time.sleep(2)
            start = time.time()
            camera.capture_sequence(outputs(num, delay, index), 'jpeg', use_video_port=True)
            finish = time.time()
            print(f'Captured {num} images at %.2ffps' % (num / (finish - start)))
        
        return findAverage(index)

    finally:
        pass


def drive(t):
    px.forward(1)
    time.sleep(t)
    px.forward(0)
    

def main():
    index = 0
    drive(1)
    for i in range(-2, -90, -1):
            px.set_camera_servo1_angle(i)
            time.sleep(0.01)
    for j in range(3):
        if check(20, index):
            tts.say("Leak detected")
            index += 1
            drive(0.6)
        drive(1)
    for i in range(-90, 1, 1):
            px.set_camera_servo1_angle(i)
            time.sleep(0.01)
    
    
    
    

if __name__ == "__main__":
    main()