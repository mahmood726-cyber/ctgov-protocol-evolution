import unittest
from src.history_diff import diff_history


def rec(d, primary=None, enrollment=None, ident="NCT01234567"):
    protocol = {
        "identificationModule": {"nctId": ident},
        "outcomesModule": {
            "primaryOutcomes": primary if primary is not None else [{"measure": "Death", "timeFrame": "1y"}]
        },
        "designModule": {
            "enrollmentInfo": enrollment if enrollment is not None else {"count": 100, "type": "ESTIMATED"}
        },
    }
    return {"nctId": "NCT01234567", "versionDate": d, "study": {"protocolSection": protocol}}


class HistoryDiffTest(unittest.TestCase):
    def test_primary_outcome_change_and_provenance(self):
        results = diff_history([rec("2023-01-01"), rec("2024-01-01", primary=[{"measure": "Death", "timeFrame": "2y"}])])
        events = [e for e in results["changes"] if e["field"] == "primary_outcomes"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["fromVersion"], "2023-01-01")
        self.assertEqual(events[0]["toVersion"], "2024-01-01")
        self.assertFalse(results["metadata"]["source_verified"])

    def test_order_or_whitespace_does_not_imply_amendment(self):
        a = rec("2023-01-01", [{"measure": "A"}, {"measure": "B"}])
        b = rec("2023-07-01", [{"measure": " B "}, {"measure": "A"}])
        result = diff_history([b, a])
        self.assertFalse(any(e["field"] == "primary_outcomes" for e in result["changes"]))

    def test_estimated_to_actual_not_automatically_an_amendment(self):
        result = diff_history([rec("2023-01-01"), rec("2023-10-01", enrollment={"count": 93, "type": "ACTUAL"})])
        e = next(x for x in result["changes"] if x["field"] == "enrollment")
        self.assertEqual(e["changeKind"], "ENROLLMENT_ESTIMATE_ACTUAL_TRANSITION")

    def test_missing_module_remains_unassessable(self):
        a, b = rec("2023-01-01"), rec("2023-10-01")
        del b["study"]["protocolSection"]["outcomesModule"]
        result = diff_history([a, b])
        self.assertFalse(any(x["field"] == "primary_outcomes" for x in result["changes"]))
        self.assertGreater(result["metadata"]["field_comparisons_unassessable_missing_version_data"], 0)

    def test_duplicate_version_and_mismatched_id_fail(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            diff_history([rec("2023-01-01"), rec("2023-01-01")])
        with self.assertRaisesRegex(ValueError, "Embedded"):
            diff_history([rec("2023-01-01", ident="NCT99999999")])

    def test_single_current_record_has_zero_history_pairs(self):
        result = diff_history([rec("2023-01-01")])
        self.assertEqual(result["metadata"]["adjacent_version_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
