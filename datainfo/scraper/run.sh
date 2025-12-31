#!/bin/bash
cd "$(dirname "$0")"
export BEARER_TOKEN="eyJhbGciOiJIUzM4NCJ9.eyJzdWIiOiIxMDAzOTIzIiwiaWF0IjoxNzY2NjA5MDQzLCJleHAiOjE3NjcyMTM4NDN9.AfPhcSgqqE0YeV3CBhQCZwh4x9mqcrxWZdcKuQ6hQlc_j6M8jLkuTFCXtvlPJUQ4"
node superScraper.js
