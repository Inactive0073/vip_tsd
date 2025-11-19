from scan_interface import ScanSession

s = ScanSession(hashMap, dbname="egais") # type: ignore

code = hashMap.get("barcode") # type: ignore
action = hashMap.get("action") \
    or hashMap.get("OnResultPositive") \
    or hashMap.get("OnResultNegative") # type: ignore

if not action:
    toast(f"Actions is {action}.") # type: ignore
else:
    action: str
    if "удалить" in action.lower():        
        # Удаляем запись из текущего документа
        s.remove_scan(code)
        # Обновляем таблицу документов
        hashMap.put("docTable", s.build_table_json_for_items("^DOC_TABLE_ROW")) # type: ignore
    else:
        pass

