import os
import json
import uuid
import csv
import io
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from config import Config, IS_VERCEL
from models import db, UploadedFile, Intent
from logger import logger

# 创建Flask应用（纯API模式，前端单独部署）
app = Flask(__name__)
app.config.from_object(Config)

# 配置CORS - 允许所有来源（生产环境可以限制为前端域名）
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

db.init_app(app)

# 确保必要的目录存在（仅在非Vercel环境下）
def ensure_directories():
    if IS_VERCEL:
        # Vercel环境下只确保/tmp目录存在
        tmp_dirs = ['/tmp/uploads', '/tmp/logs']
        for d in tmp_dirs:
            if not os.path.exists(d):
                try:
                    os.makedirs(d)
                except Exception:
                    pass
        return
    
    dirs = [
        Config.UPLOAD_FOLDER,
        os.path.dirname(Config.LOG_FILE),
        os.path.join(os.path.dirname(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')))
    ]
    for d in dirs:
        if d and not os.path.exists(d):
            os.makedirs(d)
            logger.info(f"创建目录: {d}")

# 步骤类型定义
STEP_TYPES = [
    {'value': 'data_cleaning', 'label': '数据清洗'},
    {'value': 'atomic_intent', 'label': '原子意图拆解'},
    {'value': 'object_modeling', 'label': 'Object建模'},
    {'value': 'action_modeling', 'label': 'Action建模'},
    {'value': 'triple_creation', 'label': '三元组创建'}
]

# 初始化数据库（在应用上下文中）
def init_db():
    with app.app_context():
        db.create_all()
        logger.info("数据库表创建完成")

# Vercel环境下需要在模块加载时初始化
if IS_VERCEL:
    ensure_directories()
    init_db()

@app.route('/')
def serve():
    """根路由 - 返回API状态"""
    return jsonify({
        'message': 'Ontology Review API is running',
        'status': 'ok',
        'version': '1.0.0',
        'endpoints': ['/api/health', '/api/step-types', '/api/files', '/api/intents']
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'is_vercel': IS_VERCEL})

@app.route('/api/step-types', methods=['GET'])
def get_step_types():
    """获取所有步骤类型"""
    logger.info("获取步骤类型列表")
    return jsonify({'success': True, 'data': STEP_TYPES})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传JSON文件"""
    try:
        if 'file' not in request.files:
            logger.warning("上传请求中没有文件")
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        step_type = request.form.get('step_type', 'atomic_intent')
        
        if file.filename == '':
            logger.warning("上传的文件名为空")
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        if not file.filename.endswith('.json'):
            logger.warning(f"上传的文件格式不正确: {file.filename}")
            return jsonify({'success': False, 'message': '请上传JSON文件'}), 400
        
        # 读取并解析JSON
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        logger.info(f"成功解析JSON文件: {file.filename}")
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        # 保存原始文件（在Vercel环境下保存到/tmp）
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"无法保存文件到磁盘: {e}")
        
        # 提取metadata
        metadata = data.get('metadata', {})
        source_file = metadata.get('source_file', file.filename)
        
        # 创建文件记录
        uploaded_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename,
            step_type=step_type,
            source_file=source_file,
            total_items=0,
            reviewed_items=0
        )
        db.session.add(uploaded_file)
        db.session.flush()  # 获取ID
        
        # 解析意图数据
        intent_count = 0
        for key, value in data.items():
            if key != 'metadata' and isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'id' in item:
                        intent = Intent(
                            file_id=uploaded_file.id,
                            intent_id=item.get('id', ''),
                            stage=key,
                            category=item.get('category', ''),
                            original_comment=item.get('original_comment', ''),
                            judgement=item.get('judgement', ''),
                            judged_by=item.get('judged_by', ''),
                            modified_content=item.get('modified_content', ''),
                            review_status='待核对'
                        )
                        db.session.add(intent)
                        intent_count += 1
        
        uploaded_file.total_items = intent_count
        db.session.commit()
        
        logger.info(f"文件上传成功: {file.filename}, 共 {intent_count} 条意图")
        
        return jsonify({
            'success': True,
            'message': f'文件上传成功，共导入 {intent_count} 条意图',
            'data': uploaded_file.to_dict()
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return jsonify({'success': False, 'message': f'JSON格式错误: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    """获取所有上传的文件列表"""
    try:
        step_type = request.args.get('step_type')
        query = UploadedFile.query
        
        if step_type:
            query = query.filter_by(step_type=step_type)
        
        files = query.order_by(UploadedFile.created_at.desc()).all()
        logger.info(f"获取文件列表，共 {len(files)} 个文件")
        
        return jsonify({
            'success': True,
            'data': [f.to_dict() for f in files]
        })
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除上传的文件"""
    try:
        file = UploadedFile.query.get(file_id)
        if not file:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        # 删除物理文件
        file_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"无法删除文件: {e}")
        
        db.session.delete(file)
        db.session.commit()
        
        logger.info(f"删除文件成功: {file.original_filename}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/intents', methods=['GET'])
def get_intents():
    """获取意图列表（分页）"""
    try:
        file_id = request.args.get('file_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if not file_id:
            return jsonify({'success': False, 'message': '请指定文件ID'}), 400
        
        query = Intent.query.filter_by(file_id=file_id)
        pagination = query.order_by(Intent.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logger.info(f"获取意图列表: file_id={file_id}, page={page}, per_page={per_page}")
        
        return jsonify({
            'success': True,
            'data': {
                'items': [i.to_dict() for i in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        logger.error(f"获取意图列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/intents/<int:intent_id>', methods=['GET'])
def get_intent(intent_id):
    """获取单条意图详情"""
    try:
        intent = Intent.query.get(intent_id)
        if not intent:
            return jsonify({'success': False, 'message': '意图不存在'}), 404
        
        logger.info(f"获取意图详情: {intent_id}")
        return jsonify({'success': True, 'data': intent.to_dict()})
    except Exception as e:
        logger.error(f"获取意图详情失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/intents/<int:intent_id>/review', methods=['POST'])
def review_intent(intent_id):
    """核对意图"""
    try:
        intent = Intent.query.get(intent_id)
        if not intent:
            return jsonify({'success': False, 'message': '意图不存在'}), 404
        
        data = request.json
        intent.judgement = data.get('judgement', '')
        intent.judged_by = data.get('judged_by', 'user1')
        intent.modified_content = data.get('modified_content', '')
        intent.judge_date = datetime.now()
        intent.review_status = '已核对'
        
        # 更新文件的已核对数量
        file = intent.file
        file.reviewed_items = Intent.query.filter_by(
            file_id=file.id
        ).filter(Intent.review_status != '待核对').count()
        
        db.session.commit()
        
        logger.info(f"意图核对成功: {intent_id}, judgement={intent.judgement}")
        return jsonify({'success': True, 'message': '核对成功', 'data': intent.to_dict()})
    except Exception as e:
        logger.error(f"意图核对失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/intents/<int:intent_id>/pass', methods=['POST'])
def pass_intent(intent_id):
    """直接通过意图"""
    try:
        intent = Intent.query.get(intent_id)
        if not intent:
            return jsonify({'success': False, 'message': '意图不存在'}), 404
        
        intent.judgement = '通过'
        intent.judged_by = request.json.get('judged_by', 'user1') if request.json else 'user1'
        intent.judge_date = datetime.now()
        intent.review_status = '直接通过'
        
        # 更新文件的已核对数量
        file = intent.file
        file.reviewed_items = Intent.query.filter_by(
            file_id=file.id
        ).filter(Intent.review_status != '待核对').count()
        
        db.session.commit()
        
        logger.info(f"意图直接通过: {intent_id}")
        return jsonify({'success': True, 'message': '已通过', 'data': intent.to_dict()})
    except Exception as e:
        logger.error(f"意图直接通过失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/files/<int:file_id>/export', methods=['GET'])
def export_file(file_id):
    """导出核对后的文件（支持JSON和CSV格式）"""
    try:
        file = UploadedFile.query.get(file_id)
        if not file:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        export_format = request.args.get('format', 'json').lower()
        intents = Intent.query.filter_by(file_id=file_id).order_by(Intent.id).all()
        
        if export_format == 'csv':
            # 导出为CSV格式
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                '意图ID', '阶段', '类别', '原始内容', 
                '核对结果', '核对人', '修改后内容', '核对时间', '核对状态'
            ])
            
            # 写入数据
            for intent in intents:
                writer.writerow([
                    intent.intent_id,
                    intent.stage,
                    intent.category,
                    intent.original_comment,
                    intent.judgement,
                    intent.judged_by,
                    intent.modified_content,
                    intent.judge_date.strftime('%Y-%m-%d %H:%M:%S') if intent.judge_date else '',
                    intent.review_status
                ])
            
            # 生成文件名 - 使用ASCII安全的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ascii_filename = f"intent_review_{file_id}_{timestamp}.csv"
            
            logger.info(f"导出CSV文件: {file_id}")
            
            # 添加BOM以支持Excel正确识别UTF-8编码
            csv_content = '\ufeff' + output.getvalue()
            
            # 返回CSV文件
            output.seek(0)
            response = Response(
                csv_content,
                mimetype='text/csv; charset=utf-8',
            )
            response.headers['Content-Disposition'] = f'attachment; filename={ascii_filename}'
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            return response
        else:
            # 导出为JSON格式
            # 按阶段分组
            stages = {}
            for intent in intents:
                if intent.stage not in stages:
                    stages[intent.stage] = []
                stages[intent.stage].append({
                    'id': intent.intent_id,
                    'category': intent.category,
                    'original_comment': intent.original_comment,
                    'judgement': intent.judgement,
                    'judged_by': intent.judged_by,
                    'modified_content': intent.modified_content,
                    'judge_date': intent.judge_date.strftime('%Y-%m-%d %H:%M:%S') if intent.judge_date else ''
                })
            
            # 构建输出数据
            output_data = {
                'metadata': {
                    'source_file': file.source_file,
                    'created_at': file.created_at.strftime('%Y-%m-%d'),
                    'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_items': file.total_items,
                    'reviewed_items': file.reviewed_items,
                    'judgement_options': ['通过', '需修改', '删除', '待定']
                }
            }
            output_data.update(stages)
            
            # 生成文件名 - 使用ASCII安全的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ascii_filename = f"intent_review_{file_id}_{timestamp}.json"
            
            logger.info(f"导出JSON文件: {file_id}")
            
            # 返回JSON文件下载
            json_output = json.dumps(output_data, ensure_ascii=False, indent=2)
            response = Response(
                json_output,
                mimetype='application/json; charset=utf-8',
            )
            response.headers['Content-Disposition'] = f'attachment; filename={ascii_filename}'
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
    except Exception as e:
        logger.error(f"导出文件失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 本地开发或Railway部署时运行
if __name__ == '__main__':
    ensure_directories()
    init_db()
    # 从环境变量获取端口，默认5001
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    logger.info(f"启动服务器... 端口: {port}")
    app.run(debug=debug, host='0.0.0.0', port=port)
