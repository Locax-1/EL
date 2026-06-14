import json
import re

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # 允许所有来源的跨域请求

from flask import Flask
app = Flask(__name__)

from flask import Flask, request, jsonify
from collections import defaultdict
import dashscope
from dashscope import Generation

app = Flask(__name__)

# 设置你的 API Key（请替换成你自己的 Key）
dashscope.api_key = "sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM"

@app.route('/api/query-range', methods=['POST'])
def query_range():
    data = request.get_json()
    start_date = data.get('start_date') # 例如 "2026-06-12"
    end_date = data.get('end_date')     # 例如 "2026-06-13"

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # 【关键修改】使用 LIKE 进行模糊匹配，防止因为时间戳或格式差异查不到数据
        # 假设你的数据库表名是 records，日期字段是 date
        query = """
            SELECT * FROM records
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
        """

        # 为了保险，我们在日期后面补上时间，确保覆盖全天
        # 如果还是查不到，说明数据库里真的没有这几天的数据
        start_param = f"{start_date} 00:00:00"
        end_param = f"{end_date} 23:59:59"

        cursor.execute(query, (start_param, end_param))
        rows = cursor.fetchall()

        # 【调试用】打印到底查到了几条数据，去 Vercel Logs 看！
        print(f"🔥 [DEBUG] 查询范围: {start_param} ~ {end_param}, 找到数据条数: {len(rows)}")

        conn.close()

        if not rows:
            return jsonify({
                "total_amount": 0,
                "category_breakdown": [],
                "ai_advice": "未获取到 AI 建议（该时间段无数据）"
            })

        # ... 这里保留你原有的计算 total_amount 和 category_breakdown 的逻辑 ...
        # ... 以及调用 AI 的逻辑 ...

    except Exception as e:
        print(f"❌ 数据库查询错误: {e}")
        return jsonify({"error": str(e)}), 500
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)

#sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM
