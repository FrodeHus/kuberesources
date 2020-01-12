import setuptools

setuptools.setup(
    name="kuberesources",
    version="1.0",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'kresources=kuberesources.__main__:main'
        ]
    },
    author="Frode Hus",
    author_email="frode.hus@outlook.com",
    description="Simple utility for getting an overview of set requests and limits in a kubernetes cluster",
    url="https://github.com/frodehus/kuberesources",
    python_requires='>=3.6',
    classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
)
