#!/bin/sh
set -eu
case " ${RENEWED_DOMAINS:-} " in
  *" v4.yukifn.xyz "*) ;;
  *) exit 0 ;;
esac
docker exec campus-assistant-gateway-1 caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
