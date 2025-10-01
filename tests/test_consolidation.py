import unittest

from pdf_anonymizer_core.utils import consolidate_mapping


class TestConsolidation(unittest.TestCase):
    def test_consolidate_mapping(self):
        """
        Test that the consolidation logic correctly handles duplicate entities
        and updates the anonymized text.
        """
        anonymized_text = (
            "PERSON_1 is meeting with PERSON_2 and PERSON_3. ADDRESS_1 is the location."
        )
        mapping = {
            "PERSON_1": "John Doe",
            "PERSON_2": "John Doe",
            "PERSON_3": "Jane Smith",
            "ADDRESS_1": "123 Main St",
        }

        expected_text = (
            "PERSON_1 is meeting with PERSON_1 and PERSON_3. ADDRESS_1 is the location."
        )
        expected_mapping = {
            "PERSON_1": "John Doe",
            "PERSON_3": "Jane Smith",
            "ADDRESS_1": "123 Main St",
        }

        consolidated_text, consolidated_mapping = consolidate_mapping(
            anonymized_text, mapping
        )

        self.assertEqual(consolidated_text, expected_text)
        self.assertEqual(consolidated_mapping, expected_mapping)

    def test_consolidate_mapping_no_duplicates(self):
        """
        Test that the consolidation logic works correctly when there are no duplicates.
        """
        anonymized_text = (
            "PERSON_1 is meeting with PERSON_3. ADDRESS_1 is the location."
        )
        mapping = {
            "PERSON_1": "John Doe",
            "PERSON_3": "Jane Smith",
            "ADDRESS_1": "123 Main St",
        }

        expected_text = "PERSON_1 is meeting with PERSON_3. ADDRESS_1 is the location."
        expected_mapping = {
            "PERSON_1": "John Doe",
            "PERSON_3": "Jane Smith",
            "ADDRESS_1": "123 Main St",
        }

        consolidated_text, consolidated_mapping = consolidate_mapping(
            anonymized_text, mapping
        )

        self.assertEqual(consolidated_text, expected_text)
        self.assertEqual(consolidated_mapping, expected_mapping)


if __name__ == "__main__":
    unittest.main()
