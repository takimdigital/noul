#!/usr/bin/env python3
"""Tests for noul batch module."""
import json
import sys
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noul.batch import batch_decide, ordinal_tier, load_batch_input, save_batch_results


class TestOrdinalTier(unittest.TestCase):
    def test_definite_yes(self):
        self.assertEqual(ordinal_tier(0.95), "definite_yes")
        self.assertEqual(ordinal_tier(0.90), "definite_yes")
        self.assertEqual(ordinal_tier(0.99), "definite_yes")
        self.assertEqual(ordinal_tier(1.0), "definite_yes")

    def test_maybe(self):
        self.assertEqual(ordinal_tier(0.85), "maybe")
        self.assertEqual(ordinal_tier(0.70), "maybe")
        self.assertEqual(ordinal_tier(0.50), "maybe")

    def test_definite_no(self):
        self.assertEqual(ordinal_tier(0.49), "definite_no")
        self.assertEqual(ordinal_tier(0.30), "definite_no")
        self.assertEqual(ordinal_tier(0.10), "definite_no")
        self.assertEqual(ordinal_tier(0.0), "definite_no")

    def test_boundary_values(self):
        self.assertEqual(ordinal_tier(0.90), "definite_yes")
        self.assertEqual(ordinal_tier(0.8999), "maybe")
        self.assertEqual(ordinal_tier(0.50), "maybe")
        self.assertEqual(ordinal_tier(0.4999), "definite_no")


def _mock_response(noul_value):
    return {
        "answers": {"answerable": {"noul": noul_value}},
        "_noul_latency_ms": 95.5,
        "_noul_engine": "kev",
    }


class TestBatchDecide(unittest.TestCase):
    @patch("noul.batch.decide")
    def test_batch_decide_basic(self, mock_decide):
        mock_decide.side_effect = [_mock_response(0.92), _mock_response(0.15)]
        items = [{"question": "What is the budget?"}, {"question": "What color is the laptop?"}]
        results = batch_decide(items, doc="test doc", pack="answerability")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["verdict"], "ANSWERABLE")
        self.assertGreater(results[0]["noul"], 0.5)
        self.assertEqual(results[1]["verdict"], "NOT ANSWERABLE")

    @patch("noul.batch.decide")
    def test_batch_decide_ordinal(self, mock_decide):
        mock_decide.side_effect = [_mock_response(0.95), _mock_response(0.70), _mock_response(0.30)]
        items = [{"question": "Q1"}, {"question": "Q2"}, {"question": "Q3"}]
        results = batch_decide(items, doc="doc", pack="answerability", ordinal=True)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["tier"], "definite_yes")
        self.assertEqual(results[1]["tier"], "maybe")
        self.assertEqual(results[2]["tier"], "definite_no")

    @patch("noul.batch.decide")
    def test_batch_decide_missing_question(self, mock_decide):
        items = [{"question": ""}, {"question": "Valid question?"}]
        results = batch_decide(items, doc="doc", pack="answerability")
        self.assertIn("error", results[0])
        self.assertEqual(results[0]["error"], "missing question")
        self.assertEqual(len(results), 2)

    @patch("noul.batch.decide")
    def test_batch_decide_error_handling(self, mock_decide):
        mock_decide.side_effect = [Exception("engine down"), _mock_response(0.8)]
        items = [{"question": "Q1"}, {"question": "Q2"}]
        results = batch_decide(items, doc="doc", pack="answerability")
        self.assertEqual(len(results), 2)
        self.assertIn("error", results[0])
        self.assertEqual(results[1]["verdict"], "ANSWERABLE")

    @patch("noul.batch.decide")
    def test_batch_decide_with_id(self, mock_decide):
        mock_decide.side_effect = [_mock_response(0.9)]
        items = [{"question": "Q1", "id": "my-item-42"}]
        results = batch_decide(items, doc="doc", pack="answerability")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "my-item-42")


class TestLoadBatchInput(unittest.TestCase):
    def test_csv(self):
        csv_content = "question,context,id\nWhat is the budget?,doc text,1\nWhat is the deadline?,doc text,2\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            path = f.name
        try:
            items = load_batch_input(path)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["question"], "What is the budget?")
            self.assertEqual(items[0]["context"], "doc text")
            self.assertEqual(items[0]["id"], "1")
        finally:
            os.unlink(path)

    def test_jsonl(self):
        lines = [json.dumps({"question": "Q1", "context": "doc"}), json.dumps({"question": "Q2"})]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("\n".join(lines))
            path = f.name
        try:
            items = load_batch_input(path)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["question"], "Q1")
            self.assertEqual(items[1]["question"], "Q2")
        finally:
            os.unlink(path)

    def test_unsupported_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                load_batch_input(path)
        finally:
            os.unlink(path)


class TestSaveBatchResults(unittest.TestCase):
    def test_save_and_reload(self):
        results = [{"question": "Q1", "verdict": "ANSWERABLE", "noul": 0.92}, {"question": "Q2", "verdict": "NOT ANSWERABLE", "noul": 0.15}]
        with tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False) as f:
            path = f.name
        save_batch_results(results, path)
        try:
            with open(path) as f:
                lines = [json.loads(l) for l in f if l.strip()]
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0]["question"], "Q1")
            self.assertEqual(lines[1]["verdict"], "NOT ANSWERABLE")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
