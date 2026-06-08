"""Diagnostic script: test FastAPI startup chain."""
import os, sys, traceback

os.chdir(r"D:\EquipmentManagement-Django")
sys.path.insert(0, r"D:\EquipmentManagement-Django")

print("=== Import chain ===")
try:
    from backend.app.core.config import settings
    print(f"1. config OK: {settings.SQLALCHEMY_DATABASE_URL[:80]}...")
except Exception as e:
    print(f"1. config FAIL: {e}")
    traceback.print_exc()

try:
    from backend.app.db.session import engine, Base
    print(f"2. session OK: {engine.url}")
except Exception as e:
    print(f"2. session FAIL: {e}")
    traceback.print_exc()

try:
    from backend.app import models
    print(f"3. models OK")
except Exception as e:
    print(f"3. models FAIL: {e}")
    traceback.print_exc()

print("\n=== create_all ===")
try:
    Base.metadata.create_all(bind=engine)
    print("4. create_all OK")
except Exception as e:
    print(f"4. create_all FAIL: {type(e).__name__}: {e}")
    traceback.print_exc()
