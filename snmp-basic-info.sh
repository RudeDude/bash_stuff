#!/bin/bash

# This OID is just the system name and description block. Common to basically every SNMP device.

snmpwalk -v 1 -c public $1 .1.3.6.1.2.1.1
