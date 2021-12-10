#!/usr/bin/env python
from requests import Session
from urllib.parse import urljoin
from http.client import HTTPConnection

HTTPConnection._http_vsn_str = "HTTP/1.0"

import logging
import json

logging.basicConfig(format="%(levelname)s:%(name)s: %(message)s",
                    filename="forget.log",
                    filemode="w",
                    encoding="utf-8",
                    level=logging.DEBUG)

username = "hombresinforma"
password = r"kwz@wtf*cwd_QYU1zva"

cloud_key_ip = '192.168.1.1'
controller_port = 443
base_url = "https://{cloud_key_ip}:{controller_port}".format(
    cloud_key_ip=cloud_key_ip, controller_port=controller_port)

site_name = "default"
prefix_path = "/proxy/network"
api_path = "/api"


def api_login(sess, base_url):
    logging.debug("logging in")

    end_path = api_path + "/auth/login"
    logging.debug(end_path)

    login_url = urljoin(base_url, end_path)
    logging.debug(login_url)

    payload = {"username": username, "password": password}
    payload_json = json.dumps(payload,
                              ensure_ascii=False,
                              indent=4,
                              sort_keys=True)

    logging.debug(payload_json)

    # sess.auth = (username, password)
    resp = sess.post(login_url, json=payload, headers={"Referer": "/login"})

    if resp.status_code == 200:
        logging.info("successfully logged in")
        # logging.info("updating headers")

        # sess.headers.update(resp.headers)

        # headers_json = json.dumps(dict(resp.headers),
        # ensure_ascii=False,
        # indent=4)
        # logging.debug(headers_json)

        return True
    else:
        logging.error(f"failed to login, got result: {resp.status_code:d}")
        return False


def api_get_clients(sess, base_url, site_name):
    logging.debug("getting clients")

    api_url = prefix_path + api_path
    logging.debug(api_url)
    end_url = api_url + f"/s/{site_name}/stat/alluser"
    logging.debug(end_url)

    get_url = urljoin(base_url, end_url)
    logging.debug(get_url)

    logging.info("making the get call")
    resp = sess.get(get_url)
    logging.info("got a response, dumping client json")

    client_list = resp.json()["data"]

    with open("clients.json", "w", encoding="utf-8") as f:
        json.dump(client_list, f, ensure_ascii=False, indent=4, sort_keys=True)

    num_clients = len(client_list)
    logging.debug(f"the number of clients is: {num_clients:d}")

    return client_list


def macs_to_forget(client_list):
    logging.debug("getting a list of clients with a name set")

    named_clients = []
    unnamed_clients = []
    macs_to_forget = []

    for client in client_list:
        if "name" in client:
            named_clients.append(client)
        else:
            unnamed_clients.append(client)
            macs_to_forget.append(client["mac"])

    num_named_clients = len(named_clients)
    num_unnamed_clients = len(unnamed_clients)
    num_macs_to_forget = len(macs_to_forget)

    with open("clients_named.json", 'w', encoding="utf-8") as f:
        json.dump(named_clients,
                  f,
                  ensure_ascii=False,
                  indent=4,
                  sort_keys=True)

    with open("clients_unnamed.json", 'w', encoding="utf-8") as f:
        json.dump(unnamed_clients,
                  f,
                  ensure_ascii=False,
                  indent=4,
                  sort_keys=True)

    with open("macs_to_forget.txt", 'w', encoding="utf-8") as f:
        text = '\n'.join(macs_to_forget)
        f.write(text)

    logging.debug(f"there are: {num_named_clients:d} named clients")
    logging.debug(f"there are: {num_unnamed_clients:d} unnamed clients")
    logging.debug(f"there are: {num_macs_to_forget:d} macs to forget")

    return macs_to_forget


def forget_macs(sess, base_url, site_name, macs_to_forget):
    logging.debug("forgetting mac addresses specified")

    api_url = prefix_path + api_path
    logging.debug(api_url)
    end_url = api_url + f"/s/{site_name}/cmd/stamgr"
    logging.debug(end_url)

    del_url = urljoin(base_url, end_url)
    logging.debug(del_url)

    cmd = {"cmd": "forget-sta"}

    macs_trun = {"macs": macs_to_forget[0:5]}
    payload_debug = cmd | macs_trun
    payload_json = json.dumps(payload_debug, ensure_ascii=False, indent=4)

    logging.debug(payload_json)

    macs_orig = {"macs": macs_to_forget}
    payload_final = cmd | macs_orig

    with open("payload.json", "w", encoding="utf-8") as f:
        json.dump(payload_final, f, ensure_ascii=False, indent=4)

    resp = sess.post(del_url, json=payload_final)

    if resp.status_code == 200:
        # logging.info("successfully logged in")

        headers_json = json.dumps(dict(resp.headers),
                                  ensure_ascii=False,
                                  indent=4)
        logging.debug(headers_json)

        return True
    else:
        logging.error(f"failed to login, got result: {resp.status_code:d}")
        return False

    forgot_list = resp.json()['data']
    return forgot_list


def get_named_clients(client_list):
    logging.debug("getting a list of clients with a name set")

    named_clients = []
    # unnamed_clients = []
    # macs_to_forget = []

    for client in client_list:
        if "name" in client:
            named_clients.append(client)

    num_named_clients = len(named_clients)
    # num_unnamed_clients = len(unnamed_clients)
    # num_macs_to_forget = len(macs_to_forget)

    with open("clients_named.json", 'w', encoding="utf-8") as f:
        json.dump(named_clients,
                  f,
                  ensure_ascii=False,
                  indent=4,
                  sort_keys=True)

    # with open("clients_unnamed.json", 'w', encoding="utf-8") as f:
    #     json.dump(unnamed_clients,
    #               f,
    #               ensure_ascii=False,
    #               indent=4,
    #               sort_keys=True)

    # with open("macs_to_forget.txt", 'w', encoding="utf-8") as f:
    #     text = '\n'.join(macs_to_forget)
    #     f.write(text)

    logging.debug(f"there are: {num_named_clients:d} named clients")
    # logging.debug(f"there are: {num_unnamed_clients:d} unnamed clients")
    # logging.debug(f"there are: {num_macs_to_forget:d} macs to forget")

    return named_clients


if __name__ == '__main__':
    logging.debug("starting")

    sess = Session()
    sess.verify = False

    success = api_login(sess=sess, base_url=base_url)

    if success:

        logging.debug('getting list of clients...')

        client_list = api_get_clients(sess=sess,
                                      base_url=base_url,
                                      site_name=site_name)

        named_clients = get_named_clients(client_list)

        # macs_to_forget = macs_to_forget(client_list=client_list)

        # forgot_list = forget_macs(sess=sess,
        #                           base_url=base_url,
        #                           site_name=site_name,
        #                           macs_to_forget=macs_to_forget)

        # with open("clients_forgot.json", "w", encoding="utf-8") as f:
        #     json.dump(
        #         forgot_list,
        #         f,
        #         ensure_ascii=False,
        #         indent=4,
        #     )

    logging.debug('done')