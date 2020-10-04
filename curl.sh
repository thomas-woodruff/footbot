#!/usr/bin/env bash

LOGIN=$FPL_LOGIN
PASSWORD=$FPL_PASSWORD

curl \
	-XPOST \
	-H 'Content-Type: application/json' \
	-d "{\"login\": \"${FPL_LOGIN}\", \"password\": \"${FPL_PASSWORD}\"}" \
	$1

