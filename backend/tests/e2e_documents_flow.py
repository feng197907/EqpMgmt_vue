import requests, os, time

BASE = "http://127.0.0.1:8000"


def login(username, password):
    r = requests.post(BASE + "/api/v1/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def upload_file(token, device_id, doc_type, version, filepath):
    headers = {"Authorization": f"Bearer {token}"}
    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f)}
        data = {'device_id': str(device_id), 'doc_type': doc_type, 'version': version}
        r = requests.post(BASE + "/api/v1/documents/upload", headers=headers, data=data, files=files)
    r.raise_for_status()
    return r.json()


def submit_doc(token, doc_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(BASE + f"/api/v1/documents/{doc_id}/submit", headers=headers)
    r.raise_for_status()
    return r.json()


def list_approvals(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(BASE + "/api/v1/approvals/", headers=headers)
    r.raise_for_status()
    return r.json()


def approve_req(token, req_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(BASE + f"/api/v1/approvals/{req_id}/approve", headers=headers)
    r.raise_for_status()
    return r.json()


def get_doc(token, doc_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(BASE + f"/api/v1/documents/{doc_id}", headers=headers)
    r.raise_for_status()
    return r.json()


def download_doc(token, doc_id, outpath):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(BASE + f"/api/v1/documents/{doc_id}/download", headers=headers)
    if r.status_code != 200:
        return r.status_code, None
    with open(outpath, 'wb') as f:
        f.write(r.content)
    return 200, outpath


def delete_doc(token, doc_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.delete(BASE + f"/api/v1/documents/{doc_id}", headers=headers)
    r.raise_for_status()
    return r.json()


def main():
    print('E2E documents flow start')
    token = login('admin', 'admin123')
    print('logged in, token len', len(token))

    # prepare temp files
    tdir = os.path.join(os.getcwd(), 'backend', 'tests', 'e2e_tmp')
    os.makedirs(tdir, exist_ok=True)
    f1 = os.path.join(tdir, 'a.txt')
    f2 = os.path.join(tdir, 'b.txt')
    open(f1, 'w', encoding='utf-8').write('file-A-content')
    open(f2, 'w', encoding='utf-8').write('file-B-content')

    d1 = upload_file(token, 1, 'manual', '1.0', f1)
    print('uploaded d1 id', d1.get('id'))
    d2 = upload_file(token, 1, 'manual', '1.0', f2)
    print('uploaded d2 id', d2.get('id'))

    s1 = submit_doc(token, d1.get('id'))
    print('submitted d1', s1)
    s2 = submit_doc(token, d2.get('id'))
    print('submitted d2', s2)

    # wait a moment
    time.sleep(0.5)

    approvals = list_approvals(token)
    print('approvals count', len(approvals))
    if len(approvals)==0:
        print('NO approvals found; aborting')
        return
    # find approval request for d1
    req = None
    for r in approvals:
        if r.get('doc_id') == d1.get('id'):
            req = r
            break
    if not req:
        req = approvals[0]
    print('approving request', req.get('id'), 'for doc', req.get('doc_id'))
    approve_req(token, req.get('id'))

    # check doc status
    docinfo = get_doc(token, d1.get('id'))
    print('doc status after approve:', docinfo.get('status'))

    # try download
    out = os.path.join(tdir, 'downloaded.txt')
    code, path = download_doc(token, d1.get('id'), out)
    print('download code', code, 'path', path)
    if path:
        print('downloaded content:', open(path, 'r', encoding='utf-8').read())

    # cleanup: delete both docs
    delete_doc(token, d1.get('id'))
    delete_doc(token, d2.get('id'))
    print('deleted test docs')

    print('E2E finished')


if __name__ == '__main__':
    main()
