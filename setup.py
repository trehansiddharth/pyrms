from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name="pyrms",
	version="0.1",
	description="Robot Module System for Python -- safe and parallelized programming of robot modules",
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Text Processing :: Linguistic',
    ],
	url="https://github.com/trehansiddharth/pyrms",
	author="Siddharth Trehan",
    author_email="trehans@mit.edu",
	license="MIT",
	packages=["rms"],
	install_requires=[
        "numpy"
	],
	zip_safe=False)
