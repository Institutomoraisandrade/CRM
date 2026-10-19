from crm.scraping.webdiet import parse_patient


def test_parse_patient_maps_raw_fields_to_source_record():
    raw = {
        "name": "Lais Sales", "phone": "11933334444", "birthdate": "1995-07-02",
        "email": "lais@example.com", "modality": "online", "diet_status": "ativo",
    }
    record = parse_patient(raw)
    assert record.name == "Lais Sales"
    assert record.email == "lais@example.com"
    assert record.raw == raw
