## Usage

```bash
mv cfg.example.json cfg.json
pip install -r requirement.txt
./contorl start
```

## Config
```
{
  "step": 60,
  "timeout": 10,        #单次curl的超时时间
  "debug": true,
  "transfers": [
    "192.168.6.222:6060"
  ],
  "http": 2222,
  "DC": "HL",
  "targets": {
    "alive-url-test": "www.baidu.com"
  }
}
```

## Metrics
```
{
    "alive.url.alive":"采集器状态（1存活，0不存活）",
    "alive.url.status":"url存活状态（当状态码为2xx时值为1存活，否则为0不存活）",
    "alive.url.http_code":"http状态码",
    "alive.url.time_connect":"建立到服务器的 TCP 连接所用的时间",
    "alive.url.time_starttransfer":"在发出请求之后,Web 服务器返回数据的第一个字节所用的时间",
    "alive.url.time_total":"完成请求所用的时间",
    "alive.url.time_namelookup":"",
}
```
