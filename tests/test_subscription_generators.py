import json
import uuid
import yaml
import pytest

from app.subscription.clash import ClashConfiguration
from app.subscription.singbox import SingBoxConfiguration
from app.subscription.v2ray import V2rayJsonConfig, V2rayShareLink
from app.subscription.outline import OutlineConfiguration
from app.templates.filters import to_yaml
from app.utils.helpers import json_dumps, json_dumps_bytes, json_loads, SafeLoader, SafeDumper


def make_test_inbound(protocol="vmess", network="ws"):
    return {
        "protocol": protocol,
        "network": network,
        "port": 443,
        "tls": "tls",
        "sni": "example.com",
        "host": "example.com",
        "path": "/ws",
        "header_type": "none",
        "alpn": "",
        "fp": "",
        "ais": False,
        "mux_enable": False,
        "fragment_setting": "",
        "noise_setting": "",
        "random_user_agent": False,
        "multiMode": False,
        "pbk": "",
        "sid": "",
        "spx": "",
    }


class TestSubscriptionGenerators:
    def test_clash_subscription_generation(self):
        c = ClashConfiguration()
        inbound = make_test_inbound(protocol="vmess", network="ws")
        settings = {"id": str(uuid.uuid4())}
        c.add("Test-Node", "1.2.3.4", inbound, settings)
        rendered = c.render()
        assert isinstance(rendered, str)
        assert "Test-Node" in rendered
        assert "1.2.3.4" in rendered
        parsed = yaml.load(rendered, Loader=SafeLoader)
        assert isinstance(parsed, dict)
        assert "proxies" in parsed

    def test_singbox_subscription_generation(self):
        s = SingBoxConfiguration()
        inbound = make_test_inbound(protocol="vless", network="tcp")
        inbound["tls"] = "reality"
        inbound["pbk"] = "test_public_key"
        inbound["sid"] = "12345678"
        settings = {"id": str(uuid.uuid4()), "flow": "xtls-rprx-vision"}
        s.add("Singbox-Node", "1.2.3.4", inbound, settings)
        rendered = s.render()
        assert isinstance(rendered, str)
        parsed = json_loads(rendered)
        assert "outbounds" in parsed
        assert any(o.get("tag") == "Singbox-Node" for o in parsed["outbounds"])

    def test_v2ray_share_links(self):
        link_gen = V2rayShareLink()
        inbound = make_test_inbound(protocol="vmess", network="ws")
        settings = {"id": str(uuid.uuid4())}
        link_gen.add("Vmess-Node", "1.2.3.4", inbound, settings)
        links = link_gen.render()
        assert len(links) == 1
        assert links[0].startswith("vmess://")

    def test_v2ray_configuration_generation(self):
        v = V2rayJsonConfig()
        inbound = make_test_inbound(protocol="vmess", network="tcp")
        settings = {"id": str(uuid.uuid4())}
        v.add("V2ray-Node", "1.2.3.4", inbound, settings)
        rendered = v.render()
        assert isinstance(rendered, str)
        parsed = json_loads(rendered)
        assert isinstance(parsed, list)

    def test_outline_subscription_generation(self):
        o = OutlineConfiguration()
        inbound = {"protocol": "shadowsocks", "port": 8388}
        settings = {"password": "secretpassword", "method": "aes-256-gcm"}
        o.add("SS-Node", "1.2.3.4", inbound, settings)
        rendered = o.render()
        assert isinstance(rendered, str)
        parsed = json_loads(rendered)
        assert parsed.get("server") == "1.2.3.4"
        assert parsed.get("password") == "secretpassword"

    def test_helpers_json_and_yaml_uuid(self):
        uid = uuid.uuid4()
        data = {"id": uid, "name": "node", "nested": {"val": 42}}

        # json
        dumped_str = json_dumps(data, indent=True)
        assert str(uid) in dumped_str
        assert json_loads(dumped_str)["id"] == str(uid)

        dumped_bytes = json_dumps_bytes(data, sort_keys=True)
        assert isinstance(dumped_bytes, bytes)
        assert str(uid).encode() in dumped_bytes

        # yaml
        yaml_str = yaml.dump(data, Dumper=SafeDumper)
        assert str(uid) in yaml_str
        loaded_yaml = yaml.load(yaml_str, Loader=SafeLoader)
        assert loaded_yaml["id"] == str(uid)

    def test_templates_filters_to_yaml(self):
        data = {"foo": "bar", "num": 123}
        out = to_yaml(data)
        assert "foo: bar" in out
        assert "num: 123" in out
