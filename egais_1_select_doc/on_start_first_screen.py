from scan_interface import ScanSession
import traceback

try:
    s = ScanSession(hashMap, dbname="egais") # type: ignore
    # create some mock docs for UI list
    mock_docs = [
        {"_id": "1", "barcode": "DOC001", "number": "A-001", "date": "2025-01-02"},
        {"_id": "2", "barcode": "DOC002", "number": "A-002", "date": "2025-01-03"},
        {"_id ": "3", "barcode": "DOC003", "number": "A-003", "date": "2025-01-04"}
    ]
    cards_data = s.build_cards_json_for_docs(mock_docs, layout="^DOC_ROW")
    hashMap.put("cardsTable", cards_data ) # type: ignore
    # optional: try to resend queued (no endpoint yet); will be no-op
    # s.retry_pending(endpoint=None)
except Exception as e:
    toast("Init failed: " + str(e)) # type: ignore
    hashMap.put("error", str(e) + traceback.format_exc()) # type: ignore
    hashMap.put("ShowScreen", "DB_ERROR_SCREEN") # type: ignore
