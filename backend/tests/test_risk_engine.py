import unittest

from backend.services.risk_engine import assess_risk


class RiskEngineTests(unittest.TestCase):
    def test_classifier_label_maps_to_termination_rules(self):
        clause = "Either party may terminate this Agreement without cause with immediate termination."
        result = assess_risk(clause, "Termination of agreement clause")

        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["category"], "termination")
        self.assertGreaterEqual(result["score"], 7)
        self.assertIn("Termination without cause", result["reason"])
        self.assertIn("Immediate termination", result["reason"])
        self.assertIn("No notice period", result["reason"])
        self.assertTrue(result["matched_rules"])
        self.assertTrue(result["recommendations"])

    def test_governing_law_label_detects_foreign_jurisdiction(self):
        clause = "This Agreement is governed by the laws of Delaware, and disputes shall be resolved there."
        result = assess_risk(clause, "Governing law and jurisdiction clause")

        self.assertEqual(result["level"], "MEDIUM")
        self.assertEqual(result["category"], "governing_law")
        self.assertIn("Foreign jurisdiction", result["reason"])
        self.assertTrue(any(rule["rule_id"] == "governing_law_foreign" for rule in result["matched_rules"]))

    def test_required_by_law_carveout_is_not_flagged_as_disclosure_risk(self):
        clause = (
            "The Receiving Party may disclose Confidential Information if required by law "
            "or pursuant to a valid court order."
        )
        result = assess_risk(clause, "Permitted disclosures and exceptions clause")

        self.assertEqual(result["level"], "LOW")
        self.assertNotIn("Broad regulatory disclosure language", result["reason"])
        self.assertTrue(any(signal["label"] == "Standard legal disclosure carve-out" for signal in result["positive_signals"]))

    def test_plain_shall_language_does_not_create_false_positive(self):
        clause = "The parties shall keep all Confidential Information strictly confidential for two years."
        result = assess_risk(clause, "Obligations of confidentiality and non-disclosure clause")

        self.assertEqual(result["level"], "LOW")
        self.assertIn("Moderate duration (2 years)", result["reason"])
        self.assertNotIn("One-sided obligation", result["reason"])
        self.assertIn("Moderate duration (2 years)", result["summary"])

    def test_one_sided_receiving_party_obligation_is_flagged(self):
        clause = "The Receiving Party shall return or destroy all Confidential Information and certify in writing."
        result = assess_risk(clause, "Return or destruction of confidential information clause")

        self.assertEqual(result["level"], "MEDIUM")
        self.assertIn("One-sided obligation", result["reason"])
        self.assertIn("Return or destruction obligation", result["reason"])
        self.assertIn("Formal compliance requirement", result["reason"])
        self.assertEqual(len(result["matched_rules"]), 3)

    def test_protective_signals_are_captured_for_balanced_clause(self):
        clause = (
            "The Receiving Party shall protect the information, the Disclosing Party shall label it, "
            "liability shall be limited to fees paid, and disclosures required by law are permitted."
        )
        result = assess_risk(clause, "Obligations of confidentiality and non-disclosure clause")

        self.assertEqual(result["level"], "LOW")
        self.assertTrue(any(signal["label"] == "Mutual obligations present" for signal in result["positive_signals"]))
        self.assertTrue(any(signal["label"] == "Liability cap present" for signal in result["positive_signals"]))
        self.assertTrue(result["recommendations"])

    def test_positive_signal_includes_score_reduction_when_applicable(self):
        clause = (
            "Either party may terminate this Agreement upon thirty days notice, and liability shall be limited to fees paid. "
            "A cure period of fifteen days applies before termination for breach."
        )
        result = assess_risk(clause, "Termination of agreement clause")

        score_reducing_signals = {
            signal["label"]: signal.get("impact", 0)
            for signal in result["positive_signals"]
        }

        self.assertEqual(score_reducing_signals.get("Liability cap present"), -1)
        self.assertEqual(score_reducing_signals.get("Cure period present"), -1)


if __name__ == "__main__":
    unittest.main()
