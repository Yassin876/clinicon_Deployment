#!/usr/bin/env python3
"""
التحقق من آخر 5 users تم إنشاؤهم ودورهم
"""
import sys
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.user import User
from sqlalchemy import desc

db = SessionLocal()

try:
    # آخر 5 users
    users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
    
    print(f"\n{'='*80}")
    print(f"آخر 5 users تم تسجيلهم:")
    print(f"{'='*80}\n")
    
    for user in users:
        print(f"ID: {user.id}")
        print(f"  full_name: {user.full_name}")
        print(f"  email: {user.email}")
        print(f"  phone_number: {user.phone_number}")
        print(f"  role: {user.role}")
        print(f"  created_at: {user.created_at}")
        print()
    
finally:
    db.close()
