#!/bin/bash

CIRCLE_BRANCH=pr-tesr
CIRCLE_PROJECT_REPONAME=service-client
CIRCLE_PROJECT_USERNAME=equipo-capibaras

API_URL="https://api.github.com/repos/${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}/pulls" #?head=${CIRCLE_PROJECT_USERNAME}:${CIRCLE_BRANCH}"

RESPONSE=$(curl -s -H "Accept: application/vnd.github+json" "${API_URL}")

echo $RESPONSE
