from mongoengine import*
from datamodel import*
connect("test", host="192.168.1.39", port=27017)

post_1 = Post(
    title='Test',
    content='Some engaging content',
    author='ManhNV'
)
post_1.save();
print(post_1.title)