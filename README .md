# URL Shortener — AWS VPC Project

A fully functional URL shortener built with Python (Flask) and deployed on AWS using a production-grade network architecture. This project demonstrates how to set up a VPC, public and private subnets, an Internet Gateway, a NAT Gateway, and an Application Load Balancer to run a real web application across two EC2 instances.

---

## Architecture

```
Internet
    |
Internet Gateway (IGW)
    |
Application Load Balancer (public subnet)
    |
+-------------------+-------------------+
|                                       |
EC2 app-server-1              EC2 app-server-2
(private subnet)              (private subnet)
    |                                   |
    +-------------------+---------------+
                        |
                  NAT Gateway
                (public subnet)
                        |
                  Internet (for outbound only)
```

**Traffic flow:**
- Users hit the ALB DNS over the internet
- ALB routes requests to one of the two private EC2 instances
- EC2 instances have no public IP — they are only reachable via the ALB
- Outbound traffic from EC2 (e.g. installing packages) goes through the NAT Gateway

---

## Tech Stack

- **Backend:** Python 3, Flask
- **Database:** SQLite (per instance)
- **Infrastructure:** AWS VPC, EC2, ALB, NAT Gateway, IGW, IAM

---

## Features

- Paste a long URL and get a short code instantly
- Visit the short URL to be redirected to the original
- Shows which EC2 instance served the request (proves Load Balancer is working)

---

## Local Setup

**Prerequisites:** Python 3, pip

```bash
# Clone the repo
git clone https://github.com/Aakash-Ramadurai/url-shortener.git
cd url-shortener

# Create and activate virtual environment
python3 -m venv venv

# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install flask

# Run the app
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## AWS Deployment Guide

### Prerequisites
- An AWS account
- A GitHub account with this repo pushed

---

### Step 1 — Create the VPC

1. Go to **VPC → Your VPCs → Create VPC**
2. Name: `my-project-vpc`, IPv4 CIDR: `10.0.0.0/16`
3. Click **Create VPC**

---

### Step 2 — Create Subnets

**Public Subnet 1**
- Name: `public-subnet`, AZ: `ap-south-1a`, CIDR: `10.0.1.0/24`
- After creation: enable **auto-assign public IPv4**

**Public Subnet 2**
- Name: `public-subnet-2`, AZ: `ap-south-1b`, CIDR: `10.0.3.0/24`
- After creation: enable **auto-assign public IPv4**

**Private Subnet**
- Name: `private-subnet`, AZ: `ap-south-1b`, CIDR: `10.0.2.0/24`
- Do NOT enable auto-assign public IPv4

---

### Step 3 — Create and Attach Internet Gateway

1. Go to **VPC → Internet Gateways → Create Internet Gateway**
2. Name: `my-igw`
3. After creation: **Actions → Attach to VPC** → select `my-project-vpc`

---

### Step 4 — Create Route Tables

**Public Route Table**
1. Create route table: name `public-rt`, VPC: `my-project-vpc`
2. Add route: Destination `0.0.0.0/0` → Target: `my-igw`
3. Associate `public-subnet` and `public-subnet-2`

**Private Route Table**
1. Create route table: name `private-rt`, VPC: `my-project-vpc`
2. Associate `private-subnet`
3. Leave routes for now (NAT added in next step)

---

### Step 5 — Create NAT Gateway

1. Go to **VPC → NAT Gateways → Create NAT Gateway**
2. Name: `my-nat`, Subnet: `public-subnet`, Connectivity: **Public**
3. Click **Allocate Elastic IP**
4. Click **Create NAT Gateway** and wait for status **Available**

Then update the private route table:
- Go to `private-rt` → Routes → Add route
- Destination: `0.0.0.0/0` → Target: `my-nat`

---

### Step 6 — Create Security Groups

**ALB Security Group**
- Name: `alb-sg`, VPC: `my-project-vpc`
- Inbound: HTTP port 80 from `0.0.0.0/0`

**EC2 Security Group**
- Name: `ec2-sg`, VPC: `my-project-vpc`
- Inbound: Custom TCP port 5000 from `alb-sg`

---

### Step 7 — Create IAM Role for EC2

1. Go to **IAM → Roles → Create Role**
2. Trusted entity: **AWS Service → EC2**
3. Attach policy: `AmazonSSMManagedInstanceCore`
4. Name: `ec2-ssm-role`
5. Click **Create Role**

---

### Step 8 — Launch EC2 Instances

Launch **two instances** with the following settings:

| Setting | Value |
|---|---|
| AMI | Amazon Linux 2023 |
| Instance type | t2.micro |
| VPC | my-project-vpc |
| Subnet | private-subnet |
| Auto-assign public IP | Disabled |
| Security group | ec2-sg |
| IAM role | ec2-ssm-role |

Names: `app-server-1` and `app-server-2`

**User Data script (paste for both instances):**

```bash
#!/bin/bash
yum update -y
yum install -y git
yum install -y python3-pip
pip3 install flask
cd /home/ec2-user
git clone https://github.com/Aakash-Ramadurai/url-shortener.git
cd url-shortener
python3 app.py > /tmp/app.log 2>&1 &
```

---

### Step 9 — Create Application Load Balancer

**Target Group first:**
1. Go to **EC2 → Target Groups → Create Target Group**
2. Type: Instances, Name: `my-tg`, Protocol: HTTP, Port: `5000`, VPC: `my-project-vpc`
3. Register both EC2 instances as targets

**Then the Load Balancer:**
1. Go to **EC2 → Load Balancers → Create Load Balancer → Application Load Balancer**
2. Name: `my-alb`, Scheme: **Internet-facing**
3. VPC: `my-project-vpc`
4. Availability Zones: select `public-subnet` (ap-south-1a) and `public-subnet-2` (ap-south-1b)
5. Security group: `alb-sg`
6. Listener: HTTP port 80 → forward to `my-tg`
7. Click **Create Load Balancer**

---

### Step 10 — Test

1. Go to **EC2 → Load Balancers → my-alb** and copy the DNS name
2. Open it in your browser
3. Paste a long URL and click Shorten
4. Click the short link — it should redirect
5. Refresh several times — the "Served by" hostname at the bottom will alternate between the two EC2 instances

---

## Cleanup (Important — avoid AWS charges)

Delete in this order:

1. **Load Balancer** — EC2 → Load Balancers → delete `my-alb`
2. **Target Group** — EC2 → Target Groups → delete `my-tg`
3. **EC2 Instances** — terminate both
4. **NAT Gateway** — VPC → NAT Gateways → delete `my-nat`
5. **Elastic IP** — VPC → Elastic IPs → release
6. **VPC** — delete `my-project-vpc` (automatically removes subnets, route tables, IGW)

> The NAT Gateway incurs hourly charges even when idle — always delete it first.

---

## Repository Structure

```
url-shortener/
├── app.py               # Flask application
├── requirements.txt     # Python dependencies
├── setup.sh             # EC2 bootstrap reference script
├── templates/
│   └── index.html       # Frontend UI
└── README.md
```

---

## Author

Aakash Ramadurai — [github.com/Aakash-Ramadurai](https://github.com/Aakash-Ramadurai)
