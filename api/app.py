import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict
import dashscope
from dashscope import Generation

app = Flask(__name__)
# 允许跨域，支持 OPTIONS 预检请求
CORS(app)

# 设置你的 API Key
dashscope.api_key = "sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM"

# --- 新增：根路径路由 ---
# Vercel 部署 Python 时，必须能响应根路径 / 的请求，否则会报 404 或无法启动
@app.route('/')
def home():
    return jsonify({"message": "Server is running! Go to /api/query-range"}), 200

# --- 原有的 API 路由 ---
@app.route('/api/query-range', methods=['POST'])
def query_range():
    try:
        data = request.json
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        records = data.get('records', [])

        if not records:
            return jsonify({'success': False, 'error': '没有可分析的数据'})

        # --- 第一阶段：数据清洗与分类归一化 ---
        records_str = "\n".join([f"日期:{r['date']}, 类型:{r['type']}, 金额:{r['amount']}" for r in records])
        prompt_stats = f"""
        你是一个专业的财务数据分析师。以下是用户在 {start_date} 到 {end_date} 期间的原始消费记录：
        {records_str}
        请执行以下任务：
        1. 对消费类型进行语义合并（例如将“打车”、“地铁”、“公交”合并为“交通出行”；将“买菜”、“外卖”、“奶茶”合并为“餐饮美食”）。
        2. 统计每个类别的总金额。
        3. 计算总支出。
        请严格只返回一个合法的 JSON 对象，不要包含任何 Markdown 标记或多余文字。格式如下：
        {{
            "total_spent": 1000.00,
            "categories": [
                {{"name": "餐饮美食", "amount": 500.00}},
                {{"name": "交通出行", "amount": 200.00}}
            ]
        }}
        """

        response_stats = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt_stats}],
            result_format='message'
        )

        if response_stats.status_code != 200:
            raise Exception(f"API 调用失败: {response_stats.message}")

        content_stats = response_stats.output.choices[0].message.content
        # 清理可能存在的 markdown 代码块标记
        content_stats = re.sub(r'^```json\s*', '', content_stats).strip()
        content_stats = re.sub(r'\s*```$', '', content_stats).strip()
        stats_data = json.loads(content_stats)

        # --- 数据重塑 ---
        total_amount = stats_data['total_spent']
        category_breakdown = []
        for cat in stats_data['categories']:
            percentage = round((cat['amount'] / total_amount) * 100, 1)
            category_breakdown.append({
                "name": cat['name'],
                "amount": cat['amount'],
                "percentage": percentage
            })

        # --- 第二阶段：AI 财务健康评估 ---
        categories_summary = ", ".join([f"{c['name']}({c['amount']}元)" for c in stats_data['categories']])
        prompt_eval = f"""
        基于以下 {start_date} 到 {end_date} 的消费统计数据，请给出一份简短、专业且贴心的财务评估建议（建议尽量详细）：
        - 总支出：{stats_data['total_spent']} 元
        - 消费构成：{categories_summary}
        请从消费结构是否合理、是否存在冲动消费风险、以及下阶段的理财建议三个角度进行分析。
        语气要像一位老朋友一样亲切。
        """

        response_eval = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt_eval}],
            result_format='message'
        )
        
        ai_advice = "AI 正在思考中..."
        if response_eval.status_code == 200:
            ai_advice = response_eval.output.choices[0].message.content

        # --- 最终返回 ---
        return jsonify({
            'success': True,
            'total_amount': total_amount,
            'category_breakdown': category_breakdown,
            'ai_advice': ai_advice
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# 注意：不要写 if __name__ == '__main__': app.run()，Vercel 不需要这个
