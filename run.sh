#!/bin/bash

set -xe
python "bf-native" hello.bf hello.ll && clang hello.ll -o hello.exe && ./hello.exe