#!/bin/bash
yum update -y
yum install -y python3 python3-pip git
cd /home/ec2-user
git clone https://github.com/YOUR_GITHUB_USERNAME/url-shortener.git
cd url-shortener
pip3 install -r requirements.txt
python3 app.py &