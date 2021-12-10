from unificontrol import UnifiClient

import os
import subprocess
import json
import jmespath
import logging
import time

logging.basicConfig(
    format="%(levelname)s:%(name)s: %(message)s",
    filename="update_client_names.log",
    filemode="w",
    encoding="utf-8",
    level=logging.DEBUG)

from ratelimiter import RateLimiter


def limited(until):
    duration = int(round(until - time.time()))
    logging.debug('Rate limited, sleeping for {:d} seconds'.format(duration))


def op_signin():
    result = subprocess.run(["op", "get", "account"], stdout=subprocess.PIPE)
    signed_in = result.returncode == 0

    if not signed_in:
        result = subprocess.run(
            ["op", "signin", "ploy_and_crit", "--raw"], stdout=subprocess.PIPE)
        op_variable = "OP_SESSION_ploy_and_crit"
        op_session = result.stdout.decode("utf-8").strip()
        os.environ[op_variable] = f"{op_session}"


def op_get_totp():
    result = subprocess.run(
        ["op", "get", "totp", "UI (Cloud)"], stdout=subprocess.PIPE)
    totp = result.stdout.decode("utf-8").strip()
    return totp


rate_limiter = RateLimiter(max_calls=10, period=1, callback=limited)

op_signin()
op_totp = op_get_totp()
password = r"kwz@wtf*cwd_QYU1zva"  # read credential from store
combined = f"{password}|{op_totp}"

file = open("./mycertfile.pem", "rb")
bytes = file.read()
file.close()

client = UnifiClient(
    host="unifi.local",  # possible to change?
    port="443",
    username="hombresinforma",
    password=combined,
    site="default",
    cert=bytes)

client.login()

all_users_list = client.list_allusers()['data']

named_users_file = open("./json/named_users_list.json", "r", encoding="utf-8")
named_users_json = json.load(named_users_file)

for i, user in enumerate(all_users_list):
    if "mac" in user:
        user_current = jmespath.search(
            "{\
                \"_id\": _id,\
                 \"mac\": mac,\
                 \"name\": name,\
                 \"hostname\": hostname\
            }", user)

        mac = user_current["mac"]

        user_old = jmespath.search(f"[?mac=='{mac}']", named_users_json)

        if user_old:
            user_old_filtered = jmespath.search(
                "{\
                \"_id\": _id,\
                 \"mac\": mac,\
                 \"name\": name,\
                 \"hostname\": hostname\
            }", user_old[0])

            logging.debug(f"Iteration: {i}")
            logging.debug(f"Current user:\n{user_current}")
            logging.debug(f"Old user:\n{user_old_filtered}")

            _id = user_current["_id"]
            old_name = user_current["name"]
            new_name = user_old_filtered["name"]

            logging.debug(f"_id = {_id}, change {old_name} to {new_name}")

            with rate_limiter:
                client.set_client_name(_id, new_name)

        else:
            logging.debug("no matching mac was found")