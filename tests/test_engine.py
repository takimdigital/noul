#!/usr/bin/env python3
"""Tests for noul engine module."""
import json
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noul.engine import decide, doctor, ENGINES


class TestEngine(unittest.TestCase):
    def test_engines_dict_structure(self):
        self.assertIsInstance(ENGINES, dict)
        for key in ("kev", "laya", "deepopen"):
            self.assertIn(key, ENGINES)
            cfg = ENGINES[key]
            for k in ("url", "model", "default", "enforce", "notes"):
                self.assertIn(k, cfg)
            self.assertIsInstance(cfg["notes"], str)

    @patch("noul.engine.urllib.request.urlopen")
    def test_decide_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"answers": {"q": {"noul": 0.9}}, "model": "test-model"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = decide("test state", {"q": {"type": "noul", "instructions": "test"}}, engine="kev")

        self.assertEqual(result["answers"]["q"]["noul"], 0.9)
        self.assertEqual(result["model"], "test-model")
        self.assertEqual(result["_noul_engine"], "kev")
        self.assertIn("_noul_latency_ms", result)

        mock_urlopen.assert_called_once()
        args, kwargs = mock_urlopen.call_args
        request_obj = args[0]
        url_result = request_obj.get_full_url() if hasattr(request_obj, "get_full_url") else str(request_obj)
        self.assertIn("127.0.0.1:8009", url_result)
        self.assertEqual(request_obj.method, "POST")
        self.assertEqual(request_obj.headers.get("Content-type"), "application/json")

    @patch("noul.engine.urllib.request.urlopen")
    def test_decide_engine_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with self.assertRaises(RuntimeError) as cm:
            decide("state", {"q": {"type": "noul"}}, engine="kev")
        self.assertIn("Engine 'kev'", str(cm.exception))
        self.assertIn("unreachable", str(cm.exception))

    def test_doctor(self):
        results = doctor()
        self.assertIsInstance(results, dict)
        for name in ENGINES.keys():
            self.assertIn(name, results)
            info = results[name]
            self.assertIn("reachable", info)


if __name__ == "__main__":
    unittest.main()
