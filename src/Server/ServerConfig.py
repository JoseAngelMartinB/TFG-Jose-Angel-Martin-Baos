#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

# SERVER CONFIGURATION FILE

## Database configuration:
DB_HOST = "eu-cdbr-sl-lhr-01.cleardb.net"
DB_USER = "b29f8ea3340fbc"
DB_PASS = "7accadfc"
DB_NAME = "ibmx_ac5d4e98f296176"


## Web Server configuration:
PORT = 80

## Notification parameters:
NOTIFY_EMAIL = "joseangelmartin.bsc@gmail.com"
NOTIFY_PASS = "JoseAngelBScThesis"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


## Webpage parameters:
# Select the ranges for colors green, yellow and red in cars
LIMITS = {
    'Cars' : [300, 600, 900, 1200],
    'CO' : [4.35, 6.52, 8.7, 17.4],
    'LPG' : [250, 500, 750, 1000]
}
CHART_COLORS = ['#00FFFF','#A52A2A','#DEB887','#7FFFD4','#FFE4C4','#5F9EA0','#7FFF00','#FAEBD7','#D2691E','#8A2BE2','#0000FF','#000000','#FF7F50','#6495ED','#FFEBCD','#FFF8DC','#DC143C','#00FFFF','#00008B','#008B8B','#B8860B','#A9A9A9','#006400','#BDB76B','#8B008B','#556B2F','#FF8C00','#9932CC','#8B0000','#E9967A','#8FBC8F','#483D8B','#2F4F4F','#00CED1','#9400D3','#FF1493','#00BFFF','#696969','#1E90FF','#B22222','#FFFAF0','#228B22','#FF00FF']
MAX_SMOOT_SECONDS = 1800
