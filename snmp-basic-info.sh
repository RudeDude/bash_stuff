#!/bin/bash

snmpwalk -v 1 -c public $1 .1.3.6.1.2.1.1
