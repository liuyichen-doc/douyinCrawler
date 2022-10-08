# Spider_DouYin
抖音爬虫，根据指定一名或多名用户ID，爬取个人信息以及所有作品。



实现方式：Selenium + Chromedriver


1 抖音网站的复杂的人类检测问题
2 当前只能爬取一级评论






Windows平台下需要移除与虚拟桌面相关的代码。

```python
from pyvirtualdisplay import Display

display = Display(visible=0, size=(1920, 1080))
display.start()

display.stop()
```

存在问题：
1，抖音cookies的设置有问题，不能完成登录设置