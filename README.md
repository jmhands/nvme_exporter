# nvme_exporter
Prometheus exporter for nvme-cli smart-log and OCP C0 log page

Requires the latest version of https://github.com/linux-nvme/nvme-cli

If you are on Ubuntu 22.04 or older use this method to use the nvme-cli app image

```
sudo apt install fuse
wget https://monom.org/linux-nvme/upload/AppImage/nvme-cli-latest-x86_64.AppImage
sudo chmod +x nvme-cli-latest-x86_64.AppImage
mv nvme-cli-latest-x86_64.AppImage /usr/local/bin/nvme
nvme -version
nvme version 2.7.1 (git 2.7.1)
libnvme version 1.7 (git 1.7)
```
compile from source, or install via `sudo apt install nvme-cli` if your distro supports a recent version with OCP log page support

Prerequisistes
`pip install prometheus_client`

I picked a totally random port of 18074, as the project moves out of POC we can choose a real port

Using this stack for monitoring
https://github.com/jmhands/scripts/tree/main/monitor_gpu

example prometheus.yml

```
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    scrape_interval: 15s
    static_configs:
    - targets: ["localhost:9090"]

  - job_name: "node"
    static_configs:
    - targets: ["node-exporter:9100"]

  - job_name: "nvme-cli"
    scrape_interval: 60s
    static_configs:
    - targets: ["192.168.1.10:18074"]
```

to run `python3 nvme_exporter.py`
