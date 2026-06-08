from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.app.api.deps import get_db, require_admin, get_current_user
from database import get_db as legacy_get_db
from utils.audit import log_action

router = APIRouter()


@router.get("/", dependencies=[Depends(require_admin)])
def list_requests():
    conn = legacy_get_db()
    cur = conn.cursor()
    cur.execute("SELECT ar.*, d.doc_name FROM approval_requests ar JOIN documents d ON d.id = ar.doc_id WHERE ar.status = 'pending' ORDER BY ar.id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


@router.post("/{request_id}/approve", dependencies=[Depends(require_admin)])
def approve_request(request_id: int, current_user=Depends(get_current_user)):
    conn = legacy_get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM approval_requests WHERE id = %s", (request_id,))
    req = cur.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")
    # find next pending step
    cur.execute("SELECT * FROM approval_steps WHERE request_id = %s AND status = 'pending' ORDER BY step_order ASC LIMIT 1", (request_id,))
    step = cur.fetchone()
    if not step:
        conn.close()
        raise HTTPException(status_code=400, detail="No pending approval step")
    # mark step approved
    cur.execute("UPDATE approval_steps SET status = 'approved', decided_by = %s, decided_at = CURRENT_TIMESTAMP WHERE id = %s", (current_user.username, step['id']))
    # mark request approved and set document active; archive previous active versions
    # fetch doc info
    cur.execute("SELECT device_id, doc_type FROM documents WHERE id = %s", (req['doc_id'],))
    docinfo = cur.fetchone()
    device_id = docinfo['device_id'] if docinfo else None
    doc_type = docinfo['doc_type'] if docinfo else None
    cur.execute("UPDATE approval_requests SET status = 'approved' WHERE id = %s", (request_id,))
    if device_id is not None and doc_type is not None:
        cur.execute("UPDATE documents SET status = 'archived' WHERE device_id = %s AND doc_type = %s AND status = 'active' AND id != %s", (device_id, doc_type, req['doc_id']))
    cur.execute("UPDATE documents SET status = 'active' WHERE id = %s", (req['doc_id'],))
    conn.commit()
    conn.close()
    log_action(current_user.username, "approve_request", "approval", request_id, f"批准审批请求 {request_id}")
    return {"status": "approved"}


@router.post("/{request_id}/reject", dependencies=[Depends(require_admin)])
def reject_request(request_id: int, current_user=Depends(get_current_user)):
    conn = legacy_get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM approval_requests WHERE id = %s", (request_id,))
    req = cur.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")
    # mark current pending step rejected
    cur.execute("SELECT * FROM approval_steps WHERE request_id = %s AND status = 'pending' ORDER BY step_order ASC LIMIT 1", (request_id,))
    step = cur.fetchone()
    if step:
        cur.execute("UPDATE approval_steps SET status = 'rejected', decided_by = %s, decided_at = CURRENT_TIMESTAMP WHERE id = %s", (current_user.username, step['id']))
    cur.execute("UPDATE approval_requests SET status = 'rejected' WHERE id = %s", (request_id,))
    cur.execute("UPDATE documents SET status = 'draft' WHERE id = %s", (req['doc_id'],))
    conn.commit()
    conn.close()
    log_action(current_user.username, "reject_request", "approval", request_id, f"拒绝审批请求 {request_id}")
    return {"status": "rejected"}
