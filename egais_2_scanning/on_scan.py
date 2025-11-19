from scan_interface import ScanSession

s = ScanSession(hashMap, dbname="egais") # type: ignore
code = hashMap.get("barcode") # type: ignore

if code:
    doc = s.add_scan(code)
    if not doc:
        s.create_dialog("ШК уже существует", "Удалить", "Отмена")
        s._speak(f"Штрихкод уже существует.")
        s._beep_error()
    else:
        hashMap.put("docTable", s.build_table_json_for_items("^DOC_TABLE_ROW")) # type: ignore
        if isinstance(doc, dict):
            s.fill_current_doc(doc)
            
        hashMap.put("RefreshScreen", "") # type: ignore
else:
    hashMap.put("err_description", "Код не найден.") # type: ignore
    hashMap.put("ShowScreen", "ЕГАИС3_Отгрузка_СообщениеОбОшибке") # type: ignore