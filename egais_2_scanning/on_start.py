from scan_interface import ScanSession

s = ScanSession(hashMap, dbname="egais") # type: ignore

doc = s.get_active_doc()
if doc:
    doc_name = doc.get("barcode", "not name")

    hashMap.put("docName", doc_name) # type: ignore
    hashMap.put("docTable", s.build_table_json_for_items("^DOC_TABLE_ROW")) # type: ignore

else:
    toast("No active document found") # type: ignore

# UI
if not s.get_active_barcode():
    hashMap.put("scan_nom", "Ном.") # type: ignore
    hashMap.put("scan_plan", "План") # type: ignore
    hashMap.put("scan_fact", "Факт") # type: ignore