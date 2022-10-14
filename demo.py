import os
import requests
def download_image(image_url, iamge_file_name):
        if os.path.isfile(iamge_file_name):
            # # Ignore the file if the file exist
            print("%s was downloaded ok\n" % iamge_file_name)
            return True
        response = requests.get(url=image_url, stream=True)
        with open(iamge_file_name, 'wb') as f:
            f.write(response.content)

if __name__ == '__main__':
    download_image("https://p9-pc-sign.douyinpic.com/tos-cn-i-0813c001/7fc97efb56a843d4bfadc79b6d44c6c5~noop.webp?biz_tag=aweme_images&from=3213915784&s=PackSourceEnum_AWEME_DETAIL&se=false&x-expires=1668157200&x-signature=8n1uF37aPGcG7638rBk90GnZxzM%3D","./13.webp")