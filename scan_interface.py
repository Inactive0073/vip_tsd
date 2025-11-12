import json
import random
import time
from typing import Any
import uuid
from dataclasses import dataclass

# Java bridge helper in SimpleUI
try:
    from ru.travelfood.simple_ui import SimpleUtilites as suClass # type: ignore
except Exception:
    suClass = None

try:
    # If project provides pysimplebase
    from pysimplebase import SimpleBase, DBSession
except Exception:
    # Some SimpleUI installations provide SimpleBase on classpath accessible through same name.
    SimpleBase = None
    DBSession = None

# Keys
ID_KEY = "_id"
BARCODE_KEY = "barcode"
NUMBER_KEY = "number"
META_KEY = "meta"
DATE_KEY = "date"
SCAN_NOM = "scan_nom"
SCAN_PLAN = "scan_plan"
SCAN_FACT = "scan_fact"

# Popup Keys
POPUP_RESULT = "action"


@dataclass
class Document:
    barcode: str
    number: int
    meta: dict
    date: str


    def to_dict(self):
        return {
            BARCODE_KEY: self.barcode,
            NUMBER_KEY: self.number,
            META_KEY: self.meta,
            DATE_KEY: self.date,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            barcode=data.get(BARCODE_KEY, "unknown"),
            number=data.get(NUMBER_KEY, 0),
            meta=data.get(META_KEY, {}),
            date=data.get(DATE_KEY, "unknown"),
        )

# --- SimpleBase adapter (wrap differences) ---
class SimpleBaseAdapter:
    def __init__(self, dbname="egais", timeout=200):
        if suClass is None:
            raise RuntimeError("SimpleUtilites bridge (suClass) not available in this environment")
        path = suClass.get_simplebase_dir()
        if None in (SimpleBase, DBSession):
            # try to import locally named class via ru... if present
            raise RuntimeError("SimpleBase (PySimpleBase) not available; install pysimplebase or check runtime")
        else:
            self._db = SimpleBase(dbname, path=path, timeout=timeout) # type: ignore

    # --- low-level helpers: normalize API differences ---
    def insert(self, collection: str, data: dict | list[dict] , session=False):
        """Insert one doc or list of docs"""
        if not session:
            return self._db[collection].insert(data)
        else:
            if isinstance(data, list):
                with DBSession() as s: # type: ignore
                    for doc in data:
                        self._db[collection].insert(doc, session=s)
            else:
                self._db[collection].insert(data)

    def all(self, collection: str):
        """Return list of all docs in collection"""
        return self._db[collection].all()

    def find(self, collection, query=None | dict):
        q = query or {}
        try:
            return self._db[collection].find(q).all()
        except Exception:
            try:
                return self._db[collection].find(q)
            except Exception:
                return []

    def get(self, collection, _id):
        try:
            return self._db[collection].get(_id)
        except Exception:
            try:
                return self._db[collection].get(_id)
            except Exception:
                return None

    def update(self, collection, obj: dict, new_obj: dict):
        try:
            return self._db[collection].update(obj, new_obj)
        except Exception:
            return None

    def delete(self, collection, _id):
        self._db[collection].delete([_id])

    def clear_collection(self, collection):
        """Remove all docs in a collection (helper)."""
        try:
            self._db[collection].clear()
        except Exception: # fallback: read all and delete individually
            try:
                all_docs = self.all(collection)
                for d in all_docs:
                    if isinstance(d, dict) and ID_KEY in d:
                        self.delete(collection, d[ID_KEY])
            except Exception:
                pass


# --- Application class (ScanSession) ---
class ScanSession:
    """
    High-level session API suitable for SimpleUI handlers.
    This class DOES NOT call toast/hashMap etc by itself — it returns results
    and raises exceptions. Handlers should catch and use toast().
    """
    
    COLL_CURRENT_DOC = "current_doc"
    COLL_CURRENT_ITEMS = "current_items"
    COLL_PENDING = "pending_docs"
    COLL_SENT = "sent_docs"

    CARDS_LAYOUT = "^AUTO"
    TABLE_LAYOUT = "^AUTO"

    def __init__(self, hashMap, dbname="egais"):
        self.hashMap = hashMap
        # instantiate DB adapter (this will create or open the SimpleBase DB at runtime)
        self.db = SimpleBaseAdapter(dbname)

        try:
            # checking access
            _ = self.db.all(self.COLL_CURRENT_DOC)
        except Exception:
            # silent fallback
            pass

    # --- time helper ---
    def _now(self):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # --- session life cycle ---
    def start_doc(self, data: dict[str, str], meta=None):
        """Start a new active document (clears previous active session)"""
        try:
            self.db.clear_collection(self.COLL_CURRENT_DOC)
            self.db.clear_collection(self.COLL_CURRENT_ITEMS)
        except Exception:
            # ignore if clear not supported
            pass
        _id = data.get(ID_KEY)
        barcode = data.get(BARCODE_KEY)
        number = data.get(NUMBER_KEY)
        date = data.get(DATE_KEY)

        doc = {
            ID_KEY: _id,
            BARCODE_KEY: barcode,
            NUMBER_KEY: number,
            DATE_KEY: date,
            META_KEY: meta or {},
            "status": "active"
        }
        self.db.insert(self.COLL_CURRENT_DOC, doc)
        return doc

    def get_active_doc(self) -> dict | None:
        docs = self.db.all(self.COLL_CURRENT_DOC)
        if not docs:
            return None
        return docs[0]

    def get_active_barcode(self):
        d = self.get_active_doc()
        return (d.get(BARCODE_KEY) if d else None)

    # --- items ---
    def list_items(self):
        return self.db.all(self.COLL_CURRENT_ITEMS)

    def add_scan(self, code, meta=None) -> bool | dict[str, Any]:
        """
        Add scanned code to current items.
        Returns: dict if added, False if duplicate
        """
        existing = [it.get(BARCODE_KEY) for it in self.list_items() if isinstance(it, dict)]
        if code in existing:
            return False
        rec = {ID_KEY: str(uuid.uuid4()), BARCODE_KEY: code, NUMBER_KEY: random.randint(1, 100), META_KEY: meta or {}, DATE_KEY: self._now()}
        try:
            self.db.insert(self.COLL_CURRENT_ITEMS, rec)
        except Exception as e:
            self._toast(f"Error adding scan: {e}")
        return rec

    def remove_scan(self, code):
        items = self.list_items()
        for it in items:
            if it.get(BARCODE_KEY) == code:
                _id = it.get(ID_KEY)
                if _id:
                    try:
                        self.db.delete(self.COLL_CURRENT_ITEMS, _id)
                    except Exception as e:
                        self._toast(f"Error removing scan: {e}")
                else:
                    # best-effort: cannot delete without _id
                    pass

    # --- UI helpers ---
    def build_table_json_for_items(self, layout=TABLE_LAYOUT):
        rows = []
        data = self.list_items()
        if not data:
            return
        try:
            for it in data:
                rows.append({ID_KEY: it.get(ID_KEY), BARCODE_KEY: it.get(BARCODE_KEY), NUMBER_KEY: it.get(NUMBER_KEY), DATE_KEY: it.get(DATE_KEY)})
        except Exception as e:
            self._toast(f"Error building table JSON: {e}")
            return
        wrapper = {
            "customtable": {
                "options": {"search_enabled": False, "save_position": False},
                "layout": layout,
                "tabledata": rows
            }
        }
        self._is_empty(rows)
        return json.dumps(wrapper, ensure_ascii=False)

    def _is_empty(self, data: list | tuple, msg: str = "No documents found") -> bool:
        if len(data) == 0:
            self._toast(msg)
            return True
        return False

    def build_cards_json_for_docs(self, docs_list, layout=CARDS_LAYOUT):
        rows = []
        for d in docs_list:
            rows.append({ID_KEY: d.get(ID_KEY), BARCODE_KEY: d.get(BARCODE_KEY), NUMBER_KEY: d.get(NUMBER_KEY), DATE_KEY: d.get(DATE_KEY)})
        wrapper = {
            "customcards": {
                "options": {"search_enabled": True},
                "layout": layout,
                "cardsdata": rows
            }
        }
        self._is_empty(rows)

        return json.dumps(wrapper, ensure_ascii=False)

    def fill_current_doc(self, doc: dict[str, Any]):
        """
        Fill the current document information.
        """
        self.hashMap.put(SCAN_NOM, doc.get(BARCODE_KEY, "unknown"))
        self.hashMap.put(SCAN_PLAN, doc.get(NUMBER_KEY, "unknown"))
        self.hashMap.put(SCAN_FACT, doc.get(DATE_KEY, "unknown"))

    # --- finish / queue ---
    def finish_document(self, try_send=False, endpoint=None):
        """
        Move active doc + items into pending or sent collection.
        If try_send=True and endpoint provided, will attempt to POST (requests).
        Returns dict: {"sent": bool, "envelope": ...}
        """
        doc = self.get_active_doc()
        if not doc:
            self._toast("No active document")
            raise RuntimeError("No active document")

        items = self.list_items()
        envelope = {
            "doc": {
                BARCODE_KEY: doc.get(BARCODE_KEY),
                META_KEY: doc.get(META_KEY),
                "started": doc.get("started"),
                "finished": self._now(),
                "status": "pending"
            },
            "items": items
        }

        sent = False
        if try_send and endpoint:
            try:
                import requests # type: ignore
                r = requests.post(endpoint, json=envelope, timeout=7)
                if 200 <= r.status_code < 300:
                    envelope["doc"]["status"] = "sent"
                    sent = True
            except Exception:
                # network/send failure - keep queued
                sent = False

        # persist in appropriate collection
        target = self.COLL_SENT if sent else self.COLL_PENDING
        self.db.insert(target, envelope)

        # clear active doc/items
        try:
            self.db.clear_collection(self.COLL_CURRENT_DOC)
            self.db.clear_collection(self.COLL_CURRENT_ITEMS)
        except Exception:
            pass

        return {"sent": sent, "envelope": envelope}

    def retry_pending(self, endpoint=None):
        """
        Try to send pending docs. Moves successful to sent collection.
        Returns summary {"attempted": n, "sent": m}
        """
        pending = self.db.all(self.COLL_PENDING)
        attempted = 0
        sent_count = 0
        for rec in pending:
            attempted += 1
            if not endpoint:
                continue
            try:
                import requests # type: ignore
                r = requests.post(endpoint, json=rec, timeout=7)
                if 200 <= r.status_code < 300:
                    # mark and move
                    rec["doc"]["status"] = "sent"
                    self.db.insert(self.COLL_SENT, rec)
                    _id = rec.get(ID_KEY)
                    if _id:
                        self.db.delete(self.COLL_PENDING, _id)
                    sent_count += 1
            except Exception:
                # keep in queue
                pass
        return {"attempted": attempted, "sent": sent_count}

    def create_dialog(self, title: str, approve_btn: str, cancel_btn: str, listener_name: str = "dialog_result") -> None:
        """Создает диалоговое окно для дальнейшего взаимодействия"""
        self.hashMap.put("ShowDialogStyle", json.dumps({"title": title, "yes": approve_btn, "no": cancel_btn}))
        self.hashMap.put("ShowDialogListener", listener_name)
        self.hashMap.put("ShowDialog", "")

    # --- diagnostics ---
    def debug_collections(self):
        """Return list of collection names and counts (best-effort)."""
        names = [self.COLL_CURRENT_DOC, self.COLL_CURRENT_ITEMS, self.COLL_PENDING, self.COLL_SENT]
        info = {}
        for n in names:
            try:
                info[n] = len(self.db.all(n))
            except Exception:
                info[n] = None
        return info

    def _toast(self, message):
        """Helper method to show toast messages."""
        self.hashMap.put("toast", message)

    def _speak(self, text: str):
        """Helper method to trigger speech synthesis.
        """
        self.hashMap.put("speak", text)

    def _beep(self, code: str = ""):
        """Helper method to trigger beep.
        Doc: `https://developer.android.com/reference/android/media/ToneGenerator#TONE_SUP_ERROR`
        """
        self.hashMap.put("beep", code)

    def _beep_error(self):
        """Helper method to trigger error beep.
        Code 29: Error signal
        """
        self._beep("29")

    def _beep_custom(self, code: str):
        """Helper method to trigger custom beep.
        """
        self.hashMap.put("beep", code)

# End of scan_interface.py
