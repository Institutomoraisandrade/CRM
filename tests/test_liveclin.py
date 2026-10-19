from crm.scraping.liveclin import parse_patient


def test_parse_patient_maps_raw_fields_to_source_record():
    raw = {
        "name": "Beto Guerra", "phone": "(11) 91111-2222", "birthdate": "1988-03-10",
        "plan_type": "mensal", "start_date": "2026-08-16", "end_date": "2026-09-16",
        "contracted_sessions": 1, "used_sessions": 1, "modality": "presencial",
        "service": "dieta", "price": 300.0,
    }
    record = parse_patient(raw)
    assert record.name == "Beto Guerra"
    assert record.phone == "(11) 91111-2222"  # normalization happens in matching, not here
    assert record.birthdate == "1988-03-10"
    assert record.raw == raw
