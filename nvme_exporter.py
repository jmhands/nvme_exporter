import json
import subprocess
from prometheus_client import start_http_server, Gauge
from prometheus_client import Info
import time
import os
import re

NVME_METRIC_PREFIX = 'nvme_'
PORT = 18074

class NVMeMetricsCollector:
    def __init__(self):
        self.metrics = {}

    def get_nvme_devices(self):
        # List all NVMe devices
        devices = []
        for device in os.listdir('/dev'):
            if re.match('nvme[0-9]+n1', device):
                devices.append(device)
        return devices

    def get_device_info(self, device):
        # Get device information (serial number, model, firmware)
        result = subprocess.run(['sudo', 'nvme', 'id-ctrl', f'/dev/{device}', '-o', 'json'], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "sn": data.get("sn", "").strip(),
                "mn": data.get("mn", "").strip(),
                "fw": data.get("fr", "").strip()
            }
        return None

    def collect_nvme_metrics(self):
        for device in self.get_nvme_devices():
            device_info = self.get_device_info(device)
            if device_info and device_info["sn"]:
                self.collect_and_update_metrics('smart-log', device, device_info)
                self.collect_and_update_metrics('ocp smart-add-log', device, device_info)

    def collect_and_update_metrics(self, command_type, device, device_info):
        if command_type == 'smart-log':
            result = subprocess.run(['sudo', 'nvme', 'smart-log', f'/dev/{device}', '-o', 'json'], capture_output=True, text=True)
        elif command_type == 'ocp smart-add-log':
            result = subprocess.run(['sudo', 'nvme', 'ocp', 'smart-add-log', f'/dev/{device}', '-o', 'json'], capture_output=True, text=True)
        else:
            return

        if result.returncode == 0:
            data = json.loads(result.stdout)
            self.update_metrics(data, device_info)

    def sanitize_metric_name(self, name):
        # Replace or remove invalid characters in metric names
        return re.sub(r'[^a-zA-Z0-9_:]', '_', name)

    def update_metrics(self, data, device_info):
        for key, value in data.items():
            metric_name = self.sanitize_metric_name(f'{NVME_METRIC_PREFIX}{key.replace(" ", "_").lower()}')
            if isinstance(value, dict):
                # For nested structures like "Physical media units written"
                for sub_key, sub_value in value.items():
                    extended_metric_name = self.sanitize_metric_name(f'{metric_name}_{sub_key}')
                    self.set_metric(extended_metric_name, sub_value, device_info)
            else:
                self.set_metric(metric_name, value, device_info)

    def set_metric(self, metric_name, value, device_info):
        if metric_name == 'nvme_log_page_guid':
            # Handle "Log page GUID" as an Info metric
            if metric_name not in self.metrics:
                self.metrics[metric_name] = Info(metric_name, f'NVMe metric for {metric_name}')
            self.metrics[metric_name].info({'serial_number': device_info["sn"], 'model': device_info["mn"], 'firmware': device_info["fw"], 'log_page_guid': value})
        else:
            # Handle numeric values as Gauge metrics
            try:
                numeric_value = float(value)
            except ValueError:
                # Value is not numeric; you can log this or handle differently if needed
                print(f"Ignoring non-numeric value for {metric_name}: {value}")
                return

            if metric_name not in self.metrics:
                self.metrics[metric_name] = Gauge(metric_name, f'NVMe metric for {metric_name}', ['serial_number', 'model', 'firmware'])
            self.metrics[metric_name].labels(serial_number=device_info["sn"], model=device_info["mn"], firmware=device_info["fw"]).set(numeric_value)

    def periodic_update(self):
        while True:
            self.collect_nvme_metrics()
            time.sleep(10)  # Adjust the sleep time as needed

if __name__ == "__main__":
    collector = NVMeMetricsCollector()
    start_http_server(PORT)
    print(f'Starting NVMe metrics exporter on port {PORT}')
    collector.periodic_update()
