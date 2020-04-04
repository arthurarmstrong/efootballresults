import pytesseract as pt
from PIL import Image
from bs4 import BeautifulSoup as BS
from selenium import webdriver
import re
import imageio

#browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
pt.pytesseract.tesseract_cmd = r'C:\Users\GerardArmstrong\AppData\Local\Tesseract-OCR\tesseract.exe'

page = BS(browser.page_source,'html.parser')


#get the href of the image
img_urls = [x.get('src') for x in page.find_all('img',{'src':re.compile('/RODADA')})]
img_url = img_urls[-1]
#for img_url in img_urls[2]:
print(img_url)
#Get it into a buffer
img = imageio.imread(img_url,as_gray=True)
#Run tesseract on the image
image_output = pt.image_to_string(img)
    
