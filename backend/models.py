from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UploadedFile(db.Model):
    """上传的JSON文件记录"""
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    step_type = db.Column(db.String(50), nullable=False)  # 步骤类型
    source_file = db.Column(db.String(255))  # 原始来源文件
    created_at = db.Column(db.DateTime, default=datetime.now)
    total_items = db.Column(db.Integer, default=0)
    reviewed_items = db.Column(db.Integer, default=0)
    
    intents = db.relationship('Intent', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'step_type': self.step_type,
            'source_file': self.source_file,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'total_items': self.total_items,
            'reviewed_items': self.reviewed_items
        }


class Intent(db.Model):
    """原子意图数据"""
    __tablename__ = 'intents'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    intent_id = db.Column(db.String(50), nullable=False)  # 如 INT-S1-001
    stage = db.Column(db.String(100), nullable=False)  # 阶段名称
    category = db.Column(db.String(50))  # Fact, Action, Logic等
    original_comment = db.Column(db.Text, nullable=False)
    
    # 核对相关字段
    judgement = db.Column(db.String(20), default='')  # 通过, 需修改, 删除, 待定
    judged_by = db.Column(db.String(50), default='')
    modified_content = db.Column(db.Text, default='')
    judge_date = db.Column(db.DateTime)
    
    # 状态字段
    review_status = db.Column(db.String(20), default='待核对')  # 待核对, 已核对, 直接通过
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'intent_id': self.intent_id,
            'stage': self.stage,
            'category': self.category,
            'original_comment': self.original_comment,
            'judgement': self.judgement,
            'judged_by': self.judged_by,
            'modified_content': self.modified_content,
            'judge_date': self.judge_date.strftime('%Y-%m-%d %H:%M:%S') if self.judge_date else '',
            'review_status': self.review_status
        }

