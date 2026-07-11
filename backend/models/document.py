# -*- coding: utf-8 -*-
"""
RAG 知识库文档表 (documents)
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text

from backend.database import Base


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(32), default='')        # pdf, txt, md, docx
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    vector_index_status = Column(String(32), default='pending')  # pending|indexing|ready|failed
    content = Column(Text, default='')                 # 提取后的文本内容
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.title}>'
