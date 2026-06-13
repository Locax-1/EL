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
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    records = data.get('records', [])

    if not records:
        return jsonify({'success': False, 'error': '没有可分析的数据'})

    try:
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

        response_stats = dashscope.Generation.call(
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

        # --- 第二阶段：AI 财务健康评估 ---
        # 利用刚刚清洗好的统计数据来生成评估，这样 AI 看得更准
        categories_summary = ", ".join([f"{c['name']}({c['amount']}元)" for c in stats_data['categories']])

        prompt_eval = f"""
        基于以下 {start_date} 到 {end_date} 的消费统计数据，请给出一份简短、专业且贴心的财务评估建议（100字以内）：
        - 总支出：{stats_data['total_spent']} 元
        - 消费构成：{categories_summary}

        请从消费结构是否合理、是否存在冲动消费风险、以及下阶段的理财建议三个角度进行分析。语气要像一位老朋友一样亲切。
        """

        response_eval = dashscope.Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt_eval}],
            result_format='message'
        )

        ai_advice = "AI 正在思考中..."
        if response_eval.status_code == 200:
            ai_advice = response_eval.output.choices[0].message.content

        # --- 最终返回：合并统计数据和评估建议 ---
        return jsonify({
            'success': True,
            'data': stats_data,
            'evaluation': ai_advice
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)