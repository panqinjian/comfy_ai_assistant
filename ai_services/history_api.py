"""
历史记录相关的 API 端点
"""
from aiohttp import web
import json
import os
from pathlib import Path
from typing import List, Dict
from tinydb import TinyDB, Query
from .utils.html_parser import HtmlParser
from .utils.handler_loader import load_handler_function
from .prompt_api import load_prompt_data

# 获取当前文件所在目录
CURRENT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# 历史记录路径设置在 custom_nodes/comfy_ai_assistant/ai_services/history 目录下
HISTORY_DIR = CURRENT_DIR / "history"

# 确保历史记录目录存在
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# 数据库文件路径
DB_FILE = HISTORY_DIR / "history.db"

class HistoryDB:
    """历史记录数据库管理类"""
    _instance = None
    _db = None
    _last_read_position = 0
    _current_session_id = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_db(self):
        """获取数据库连接"""
        if self._db is None:
            try:
                self._db = TinyDB(str(DB_FILE), indent=4)
                # 检查是否需要初始化
                metadata = self._db.table('_metadata')
                if not metadata.get(Query().key == 'last_message_id'):
                    metadata.upsert(
                        {'key': 'last_message_id', 'value': 0},
                        Query().key == 'last_message_id'
                    )
                    #print("已创建新的历史记录数据库")
            except Exception as e:
                print(f"初始化历史记录数据库失败: {str(e)}")
                raise e
        return self._db

    def close(self):
        """关闭数据库连接"""
        if self._db is not None:
            self._db.close()
            self._db = None

    def get_last_position(self):
        """获取最后读取位置"""
        return self._last_read_position

    def set_last_position(self, position):
        """设置最后读取位置"""
        self._last_read_position = position

    def get_session_id(self):
        """获取当前会话ID"""
        return self._current_session_id

    def set_session_id(self, session_id):
        """设置当前会话ID"""
        self._current_session_id = session_id

# 创建全局数据库管理器实例
db_manager = HistoryDB.get_instance()

def register_history_api(app):
    """注册历史记录相关的 API 路由"""
    try:
        app.router.add_get("/comfy_ai_assistant/history", get_history_tinydb)
        app.router.add_post("/comfy_ai_assistant/save_history", set_history_tinydb)
        app.router.add_get("/comfy_ai_assistant/clear_history", clear_history_tinydb)
        app.router.add_get('/comfy_ai_assistant/sessions', get_sessions)
        print("历史记录 API 路由已注册")
    except Exception as e:
        print(f"注册历史记录 API 路由失败: {e}")

def get_next_message_id() -> int:
    """获取下一个可用的消息ID"""
    try:
        db = db_manager.get_db()
        metadata = db.table('_metadata')
        current = metadata.get(Query().key == 'last_message_id')
        if not current:
            metadata.insert({'key': 'last_message_id', 'value': 0})
            return 1
        next_id = current['value'] + 1
        metadata.update({'value': next_id}, Query().key == 'last_message_id')
        return next_id
    except Exception as e:
        print(f"获取下一个消息ID失败: {str(e)}")
        raise e

async def set_history_tinydb(request):
    """
    保存历史记录到 TinyDB
    
    请求体格式:
    {
        "user": {
            "content": "用户消息",
            "images": ["图片URL1", "图片URL2"],
            "prompt_name": "提示词名称"  # 可选字段
        },
        "assistant": {
            "content": "AI回复",  # AI回复内容
            "images": []  # AI 图片，可选
        }
    }
    """
    try:
        # 获取请求数据
        data = await request.json()
        
        # 验证数据结构
        if not all(key in data for key in ['user', 'assistant']):
            return web.json_response({
                'success': False,
                'error': '缺少必要字段: user 或 assistant'
            }, status=400)
            
        # 构建存储结构
        history_data = {
            'message_id': get_next_message_id(),
            'type': 'message',
            'user': {
                'content': data['user'].get('content', ''),
                'images': data['user'].get('images', []),
                'prompt_name': data['user'].get('prompt_name')
            },
            'assistant': {
                'content': data['assistant'].get('content', ''),
                'images': data['assistant'].get('images', [])
            }
        }
        
        # 保存到数据库
        if save_history_tinydb(history_data):
            return web.json_response({
                'success': True,
                'message_id': history_data['message_id']
            })
        else:
            return web.json_response({
                'success': False,
                'error': '保存历史记录失败'
            }, status=500)
            
    except json.JSONDecodeError:
        return web.json_response({
            'success': False,
            'error': '无效的 JSON 数据'
        }, status=400)
    except Exception as e:
        print(f"保存历史记录到 TinyDB 失败: {str(e)}")
        return web.json_response({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }, status=500)

def save_history_tinydb(data: dict) -> bool:
    """
    保存历史记录到 TinyDB
    
    Args:
        data: {
            'message_id': int,
            'type': 'message',
            'user': {
                'content': str,
                'images': list,
                'prompt_name': str
            },
            'assistant': {
                'content': str,
                'images': list
            }
        }
    """
    try:
        db = db_manager.get_db()
        
        # 验证基本数据结构
        if not all(key in data for key in ['message_id', 'type', 'user', 'assistant']):
            raise ValueError("数据缺少必要字段")
            
        # 保存记录
        Message = Query()
        db.upsert(data, Message.message_id == data['message_id'])
        
        #print(f"保存历史记录成功，ID: {data['message_id']}")
        return True
        
    except Exception as e:
        print(f"保存历史记录到 TinyDB 失败: {str(e)}")
        return False

async def get_history_tinydb(request):
    """获取 TinyDB 历史记录的 API 端点"""
    try:
        message_id = request.query.get('message_id', '0')  # 默认为0
        limit = int(request.query.get('limit', '10'))
        
        # 验证limit参数
        if limit < 1 or limit > 100:
            return web.json_response({
                'success': False,
                'error': 'Invalid limit: must be between 1 and 100'
            }, status=400)
        
        # 加载历史记录
        result = load_history_tinydb(
            message_id=int(message_id),
            limit=limit,
            formatted=True
        )
        
        return web.json_response({
            'success': True,
            'data': result['records'],
            'has_more': result['has_more'],
            'next_id': result['next_id']
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

async def clear_history_tinydb(request):
    """
    清空 TinyDB 历史记录
    通过删除并重建数据库来实现快速清理
    """
    try:
        db_path = HISTORY_DIR / 'history.db'
        if db_path.exists():
            try:
                db_manager.close()
            except:
                pass
            db_path.unlink()
        
        db_manager.get_db()  # 这会创建新的数据库并初始化必要的表
        #print("历史记录数据库已重建")
        
        return web.json_response({
            'success': True,
            'message': '历史记录已清空'
        })

    except Exception as e:
        print(f"清空历史记录失败: {str(e)}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

def load_history_tinydb(message_id: int = None, limit: int = 10,formatted:bool=False) -> dict:
    """从 TinyDB 加载历史记录，从指定message_id开始往前读取limit条记录"""
    try:
        db = db_manager.get_db()
        Message = Query()
        result_records = []
        
        # 如果message_id为空或0，获取最大ID
        if not message_id or message_id == 0:
            metadata = db.table('_metadata')
            current = metadata.get(Query().key == 'last_message_id')
            if not current:
                db_manager.set_last_position(0)
                return {
                    'records': [],
                    'has_more': False,
                    'next_id': None
                }
            message_id = current['value']
        
        # 从message_id开始往前读取limit条记录
        current_id = message_id
        while len(result_records) < limit and current_id > 0:
            record = db.get((Message.message_id == current_id) & (Message.type == 'message'))
            if record:
                if formatted:
                    # 获取用户消息中的prompt_id
                    prompt_id = record['user'].get('prompt_id')
                    
                    # 使用新的通用处理方法
                    record['assistant']['content'] = HtmlParser.process_content_by_prompt(
                        record['assistant']['content'], 
                        prompt_id
                    )
                
                result_records.append(record)
            current_id -= 1
        
        # 设置last_position为当前message_id减去limit
        next_position = message_id - limit
        db_manager.set_last_position(next_position)
        
        # 检查是否还有更多记录
        has_more = next_position > 0
        next_id = next_position if has_more else None
        
        return {
            'records': result_records,
            'has_more': has_more,
            'next_id': next_id
        }
            
    except Exception as e:
        print(f"从 TinyDB 加载历史记录失败: {str(e)}")
        raise e

async def get_sessions(request):
    """获取当前会话信息"""
    try:
        # 如果没有初始化，获取最新消息ID
        if db_manager.get_last_position() == 0:
            metadata = db_manager.get_db().table('_metadata')
            current = metadata.get(Query().key == 'last_message_id')
            if current:
                db_manager.set_last_position(current['value'])
        
        return web.json_response({
            'success': True,
            'data': {
                'last_position': db_manager.get_last_position(),
                'session_id': db_manager.get_session_id(),
                'total_messages': db_manager.get_last_position()
            }
        })
        
    except Exception as e:
        print(f"获取会话信息失败: {str(e)}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

