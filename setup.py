from setuptools import setup, find_packages  
import sys
  
setup(  
    name="vscrapy",
    version='0.0.2',
    author="cilame",
    author_email="opaquism@hotmail.com",
    description="multi task scrapy redis.",
    python_requires=">=3.6",
    install_requires=[
        'Scrapy>=1.0',
        'redis>=2.10',
        'six>=1.5.2',
    ],
    long_description="multi task scrapy redis.",
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/cilame/vscrapy",
    packages=['vscrapy'],
    package_data ={
        "vscrapy":[
            '*',
            'vscrapy/*',
            'vscrapy/scrapy_mod/*',
            'vscrapy/scrapy_redis_mod/*',
            'vscrapy/spiders/*',
        ]
    },
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['vscrapy = vscrapy.cmdline:execute']
    },
)  
