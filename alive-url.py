#!/usr/bin/env python
import time
import subprocess
import threading
import flask
import multiprocessing.pool

from service import metric_handler
from service import configHelper
from service.logHelper import LogHelper

CONFIG = configHelper.CONFIG
logger = LogHelper().logger


def generate_curl_metric(url, endpoint, timeout, dc):
    COMMAND = "curl -I -m %s -o /dev/null -s -w %s %s" % (
        timeout, '%{http_code}:%{time_connect}:%{time_starttransfer}:%{time_total}:%{time_namelookup}', url)
    try:
        subp = subprocess.Popen(
            COMMAND,
            shell=True,
            stdout=subprocess.PIPE)
        output = subp.communicate()[0]
    except Exception:
        logger.error("unexpected error while execute cmd : %s" % COMMAND)
        return []

    values = output.split(':')
    metrics = []
    if len(values) == 5:
        ms = {
            'alive.url.alive': 1,
            'alive.url.status': 1 if 199 < int(values[0]) < 300 else 0,
            'alive.url.http_code': int(values[0]),
            'alive.url.time_connect': float(values[1]),
            'alive.url.time_starttransfer': float(values[2]),
            'alive.url.time_total': float(values[3]),
            'alive.url.time_namelookup': float(values[4])
        }
        for key, val in ms.items():
            m = metric_handler.gauge_metric(endpoint, key, val, DC=dc)
            m['step'] = CONFIG['step']
            metrics.append(m)
    return metrics


def alive(step):
    process_count = (multiprocessing.cpu_count() * 2 + 1) if (multiprocessing.cpu_count() * 2 + 1) < 11 else 10
    logger.info("multiprocess count is : %s" % process_count)
    DC = CONFIG["DC"]
    timeout = CONFIG["timeout"]
    targets = CONFIG['targets']
    while True:
        pool = multiprocessing.Pool(process_count)
        now = int(time.time())
        metrics = []
        result = []
        for key, val in targets.items():
            result.append(pool.apply_async(generate_curl_metric, (val, key, timeout, DC)))
        pool.close()
        pool.join()

        for res in result:
            metrics.extend(res.get())

        metric_handler.push_metrics(metrics)

        dlt = time.time() - now
        logger.info("cycle finished . cost time : %s" % dlt)
        if dlt < step:
            time.sleep(step - dlt)


# flask app
app = flask.Flask(__name__)


@app.route("/add", methods=["POST"])
def add_alive_url():
    params = flask.request.get_json(force=True, silent=True)
    if not params:
        return flask.jsonify(status="error", msg="json parse error")

    logger.info("add_alive_url receive data : %s" % str(params))

    url = params.get("url", None)
    endpoint = params.get("endpoint", None)
    if not url or not endpoint:
        return flask.jsonify(status="error", msg="incomplete imfomation")

    targets = CONFIG["targets"]
    if endpoint in targets:
        return flask.jsonify(status="error", msg="duplicated endpoint")

    targets[endpoint] = url
    logger.info("add alive_url success %s[%s]" % (endpoint, url))
    configHelper.write_config()
    return flask.jsonify(status="ok", msg="ok")


@app.route("/delete", methods=["POST"])
def delete_alive_url():
    params = flask.request.get_json(force=True, silent=True)
    if not params:
        return flask.jsonify(status="error", msg="json parse error")

    logger.info("delete_alive_url receive data : %s" % str(params))

    endpoint = params.get("endpoint", None)
    if not endpoint:
        return flask.jsonify(status="error", msg="incomplete information")

    targets = CONFIG["targets"]

    del targets[endpoint]
    logger.info("delete alive_url success %s" % endpoint)
    configHelper.write_config()
    return flask.jsonify(status="ok", msg="ok")


@app.route("/update", methods=["POST"])
def update_alive_url():
    params = flask.request.get_json(force=True, silent=True)
    if not params:
        return flask.jsonify(status="error", msg="json parse error")

    logger.info("update_alive_url receive data : %s" % str(params))

    new_url = params.get("url", None)
    endpoint = params.get("endpoint", None)
    if not (new_url and endpoint):
        return flask.jsonify(status="error", msg="incomplete imfomation")

    targets = CONFIG["targets"]
    if not endpoint in targets:
        return flask.jsonify(status="error", msg="no such endpoint")

    old_url = targets[endpoint]
    targets[endpoint] = new_url
    logger.info("update alive_url success %s[%s] to [%s]" %
                (endpoint, old_url, new_url))
    configHelper.write_config()
    return flask.jsonify(status="ok", msg="ok")


@app.route("/list")
def list_alive_url():
    return flask.jsonify(CONFIG["targets"])


if __name__ == "__main__":
    t = threading.Thread(target=alive, args=(CONFIG['step'],))
    t.daemon = True
    t.start()

    app.run(host="0.0.0.0",
            port=CONFIG['http'],
            debug=CONFIG['debug'],
            use_reloader=False)
