# 文件处理工具
import hashlib
import os

from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_upload_dir(device_id):
    """确保设备上传目录存在"""
    device_dir = os.path.join(UPLOAD_FOLDER, f"device_{device_id}")
    os.makedirs(device_dir, exist_ok=True)
    return device_dir


def compute_doc_hash(file_path, signer, meaning, signed_at):
    """计算文档哈希值（用于签名验证）"""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            hasher.update(chunk)
    hasher.update(signer.encode("utf-8"))
    hasher.update(meaning.encode("utf-8"))
    hasher.update(signed_at.encode("utf-8"))
    return hasher.hexdigest()
