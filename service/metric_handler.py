import random
import requests
from service.logHelper import LogHelper
from service.configHelper import CONFIG

logger = LogHelper().logger


# metric
def make_metric(endpoint, metric, value, datatype, **tags):
    if tags:
        tags = ["{0}={1!s}".format(k, v) for k, v in tags.items()]
        tags = ",".join(tags)
    else:
        tags = ""
    return {
        "endpoint": endpoint,
        "metric": metric,
        "tags": tags,
        "value": value,
        "counterType": datatype,
    }


def gauge_metric(endpoint, metric, value, **tags):
    return make_metric(endpoint, metric, value, "GAUGE", **tags)


def counter_metric(endpoint, metric, value, **tags):
    return make_metric(endpoint, metric, value, "COUNTER", **tags)


def push_metrics(metrics):
    # print json.dumps(metrics, indent=4)
    transfers = CONFIG['transfers'][:]
    for i in range(len(transfers)):
        try:
            addr = random.choice(transfers)
            r = requests.post("http://%s/api/push" % addr,
                              json=metrics,
                              timeout=CONFIG['step'] * 0.6)
            logger.info(r.text)
            if r.ok:
                break
        except Exception, e:
            transfers.remove(addr)
            logger.info("push %d  metrics failed: %s" % (len(metrics), str(e)))
