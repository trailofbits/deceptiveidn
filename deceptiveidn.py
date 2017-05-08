#!/usr/bin/env python3

import sys
if sys.version_info < (3, 0):
    sys.stderr.write("[!] Please run this script with python3\n")
    sys.exit(1)

import os
import encodings.idna as idna
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except:
    print("[!] Please install pillow: pip3 install pillow\n")
    raise

import glob
import subprocess
import socket
import tempfile

import itertools

# Config
fonts = ("SFText-Regular.otf", "Georgia.ttf", "Times New Roman.ttf", "Helvetica")
font_sizes = (32, 48, 54, 72)

def main():
    if len(sys.argv) != 2:
        print("Usage: {} idn_to_test | --tests")
        sys.exit(1)

    if sys.argv[1] == "--tests":
        pass

        test_inputs = open('test_inputs.txt', 'r', encoding="UTF8").readlines()
        test_inputs = map(str.strip, test_inputs) # strip each input

        for idn in test_inputs:
            test_idn(idn)

    else:
        idn = sys.argv[1]
        if 'xn--' not in idn:
            print("Error: Expected idn to start with xn--. Got: {}".format(idn))
            sys.exit(1)

        test_idn(idn)

def test_idn(s):

    # convert idn to unicode
    un = idn_to_unicode(s)

    idn_host = None
    try:
        idn_host = socket.gethostbyname(s)
    except:
        pass

    guesses = set()

    for font, size in itertools.product(fonts, font_sizes):
        im = render_idn(text=un, font_name=font, font_size=size)

        guess = make_guess(im)
        if not un.endswith(guess):
            guesses.add(guess)

    hosts = {}
    for guess in guesses:
        try:
            host = socket.gethostbyname(guess)
        except:
            continue

        hosts[guess] = host

    print("IDN: {} ({})".format(un, s))
    if len(hosts) > 0:
        print("\tDeceptive IDN, possible readings: ")
        for host in hosts:
            print("\t- {} {}".format(host, hosts[host]))
    else:
        print("\tCould not identify deceptive readings")

def render_idn(text, font_name, font_size):
    width = 500
    height = 100
    bgcolor = (255, 255, 255, 255)
    color = (0,0,0, 255)

    image = Image.new("RGBA", (width, height), bgcolor)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_name, font_size, encoding="unic")

    draw.text((0, 0), text, font=font, fill=color)

    out_file = tempfile.NamedTemporaryFile(suffix=".png")
    image.save(out_file.name)

    return out_file

def make_guess(im):
    output = tempfile.NamedTemporaryFile(suffix='.txt')
    output_name_sans_suffix = output.name[:-4]
    tesseract = ['tesseract', im.name, output_name_sans_suffix, 
            '--user-patterns', 'urlpatterns.txt', ]

    p = subprocess.Popen(tesseract, stderr=subprocess.PIPE)
    p.wait()

    stdout, stderr = p.communicate()
    guess = output.read().decode("UTF8").strip()

    return guess

def idn_to_unicode(s):
    rv = []
    for part in s.split('.'):
        if part.startswith('xn--'):
            rv.append(idna.ToUnicode(part))
        else:
            rv.append(part)

    return '.'.join(rv)

if __name__ == '__main__':
    main()
