import random
import time
import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from PIL import Image
import requests
from io import BytesIO

class Geek_Huxiu(object):

    def __init__(self):

        self.driver = webdriver.Chrome()

        self.driver.set_window_size(1366,768)


    def run(self):
        self.driver.get("https://www.huxiu.com/")

        WebDriverWait(self.driver,10).until(EC.element_to_be_clickable((By.XPATH,'//*[@class="js-register"]')))

        reg_element = self.driver.find_element_by_xpath('//*[@class="js-register"]')
        reg_element.click()

        WebDriverWait(self.driver,10).until(EC.element_to_be_clickable((By.XPATH,'//div[@class="gt_slider_knob gt_show"]')))

        # 进入模拟拖动流程
        self.analog_drag()


    def analog_drag(self):
        # 鼠标移动到拖动按钮，显示出拖动图片
        element = self.driver.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')
        ActionChains(self.driver).move_to_element(element).perform()
        time.sleep(3)


        # 刷新一下极验证图片
        element = self.driver.find_element_by_xpath('//a[@class="gt_refresh_button"]')
        element.click()
        time.sleep(1)

        # 获取图片地址和位置坐标列表
        cut_image_url,cut_location = self.get_image_url('//div[@class="gt_cut_bg_slice"]')
        full_image_url, full_location = self.get_image_url('//div[@class="gt_cut_fullbg_slice"]')
        # 根据坐标拼接图片
        cut_image = self.splicing_image(cut_image_url, cut_location)
        full_image = self.splicing_image(full_image_url, full_location)

        # 将图片存储到本地
        cut_image.save("cut.jpg")
        full_image.save("full.jpg")

        dis = self.get_distance(cut_image,full_image)
        print("缺口x坐标",dis)

        self.start_move(dis)

        # 如果出现错误
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="gt_ajax_tip gt_error"]')))
            print("验证失败")
            return
        except TimeoutException as e:
            pass

        # 判断是否验证成功
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="gt_ajax_tip gt_success"]')))
        except TimeoutException:
            print("重新验证....")
            time.sleep(5)
            # 失败后递归执行拖动
            self.analog_drag()
        else:
            print("验证成功")


        self.driver.close()
    # 移动滑块
    def start_move(self, distance):
        element = self.driver.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')


        # 使用滑块的一半进行偏移设置
        distance -= element.size.get('width') / 2
        distance += 15

        # 按下鼠标左键
        ActionChains(self.driver).click_and_hold(element).perform()
        time.sleep(0.5)
        while distance > 0:
            if distance > 20:
                # 如果距离大于20，就让他移动快一点
                span = random.randint(5, 8)
            else:
                # 快到缺口了，就移动慢一点
                span = random.randint(2, 3)
            ActionChains(self.driver).move_by_offset(span, 0).perform()
            distance -= span
            time.sleep(random.randint(10, 50) / 100)

        ActionChains(self.driver).move_by_offset(distance, 1).perform()
        ActionChains(self.driver).release(on_element=element).perform()



    def splicing_image(self,image_url,location):
        res = requests.get(image_url)
        file = BytesIO(res.content)
        img = Image.open(file)
        image_upper = []
        image_down = []
        for pos in location:
            if pos[1] == 0:
                # y值==0的图片属于上半部分，高度58
                image_upper.append(img.crop((abs(pos[0]), 0, abs(pos[0]) + 10, 58)))
            else:
                # y值==58的图片属于下半部分
                image_down.append(img.crop((abs(pos[0]), 58, abs(pos[0]) + 10, img.height)))

        x_offset = 0
        # 创建一张画布，x_offset主要为新画布使用
        new_img = Image.new("RGB", (260, img.height))
        for img in image_upper:
            new_img.paste(img, (x_offset, 58))
            x_offset += img.width

        x_offset = 0
        for img in image_down:
            new_img.paste(img, (x_offset, 0))
            x_offset += img.width

        return new_img

    def get_image_url(self,xpath):
        link = re.compile('background-image: url\("(.*?)"\); background-position: (.*?)px (.*?)px;')
        elements = self.driver.find_elements_by_xpath(xpath)
        image_url = None

        location = list()

        for element in elements:
            style = element.get_attribute('style')
            groups = link.search(style)

            url = groups[1]
            x_pos = groups[2]
            y_pos = groups[3]
            location.append((int(x_pos), int(y_pos)))
            if not image_url:
                image_url = url
        return image_url, location

    def get_distance(self,cut_image,full_image):

        # print(cut_image.size)
        threshold = 50
        for i in range(0,cut_image.size[0]):
            for j in range(0,cut_image.size[1]):
                pixel1 = cut_image.getpixel((i, j))
                pixel2 = full_image.getpixel((i, j))
                res_R = abs(pixel1[0] - pixel2[0])  # 计算RGB差
                res_G = abs(pixel1[1] - pixel2[1])  # 计算RGB差
                res_B = abs(pixel1[2] - pixel2[2])  # 计算RGB差

                if res_R > threshold and res_G > threshold and res_B > threshold:
                    return i  # 需要移动的距离



if __name__ == '__main__':
    h = Geek_Huxiu()
    h.run()









