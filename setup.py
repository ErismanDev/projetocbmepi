from setuptools import setup, find_packages

setup(
    name='projetocbmepi',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==2.2.5',
        'flask-sqlalchemy==3.1.1',
        'flask-migrate==4.0.5',
        'flask-login==0.6.3',
        'flask-wtf==1.2.1',
        'flask-mail==0.9.1',
        'werkzeug==2.2.3',
        'sqlalchemy==2.0.23',
        'email-validator==2.1.0.post1',
        'python-dotenv==1.0.1',
        'reportlab==4.0.7',
        'xlsxwriter==3.1.2',
        'pandas==2.1.3',
        'pillow==10.1.0',
        'qrcode==7.4.2',
        'apscheduler==3.10.4',
        'flask-security-too==5.1.2',
        'flask-jwt-extended==4.4.4'
    ],
) 