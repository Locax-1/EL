import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime  # 【修复1】必须导入 datetime
import dashscope
from dashscope import Generation

app = Flask(__name__)
CORS(app)

# --- 配置区域 ---
# 设置你的 API Key
dashscope.api_key = "sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM"

@app.route('/api/query-range', methods=['POST'])
def query_range():
    try:
        data = request.get_json()
        
        raw_start = data.get('start_date')
        raw_end = data.get('end_date')
        all_records = data.get('records', {})  # 【修复3】接收前端传来的完整 records 对象

        # --- 数据清洗与分类归一化 ---
        # 将前端传来的 { "2026-06-12": [...] } 格式转换为 AI 能读的字符串
        records_list = []
        for date_key, items in all_records.items():
            for item in items:
                # 确保数据安全
                record_type = item.get('type', '其他')
                amount = item.get('amount', '0')
                records_list.append(f"日期:{date_key}, 类型:{record_type}, 金额:{amount}")
        
        records_str = "\n".join(records_list)

        # 如果没有数据，直接返回
        if not records_str.strip():
            return jsonify({
                'success': True,
                'total_amount': 0,
                'category_breakdown': [],
                'ai_advice': '该时间段内没有记账数据。'
            })

        # --- 第一阶段：数据清洗与分类归一化 ---
        # 【修复2】日期格式标准化
        try:
            start_date = datetime.strptime(raw_start, "%Y-%m-%d").strftime("%Y年%m月%d日")
            end_date = datetime.strptime(raw_end, "%Y-%m-%d").strftime("%Y年%m月%d日")
        except Exception as e:
            start_date = raw_start
            end_date = raw_end

        prompt_stats = f""" 
            你是一个专业的财务数据分析师。以下是用户在 {start_date} 到 {end_date} 期间的原始消费记录：
            {records_str}
            请执行以下任务：
            1. 对消费类型进行语义合并（例如将“打车”、“地铁”、“公交”合并为“交通出行”；将“买菜”、“外卖”、“奶茶”合并为“餐饮美食”）。
            2. 统计每个类别的总金额。
            3. 计算总支出。
            请严格只返回一个合法的 JSON 对象，不要包含任何 Markdown 标记或多余文字。
            格式如下：
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
            raise Exception(f"AI 调用失败: {response_stats.message}")

        content_stats = response_stats.output.choices[0].message.content
        # 清理 Markdown 代码块标记
        content_stats = re.sub(r'^```json\s*', '', content_stats).strip()
        content_stats = re.sub(r'\s*```$', '', content_stats).strip()
        stats_data = json.loads(content_stats)

        # --- 数据重塑 ---
        total_amount = stats_data['total_spent']
        category_breakdown = []
        for cat in stats_data['categories']:
            percentage = round((cat['amount'] / total_amount) * 100, 1) if total_amount > 0 else 0
            category_breakdown.append({
                "name": cat['name'],
                "amount": round(cat['amount'], 2),
                "percentage": percentage
            })

        # --- 第二阶段：AI 财务健康评估 ---
        categories_summary = ", ".join([f"{c['name']}({c['amount']}元)" for c in stats_data['categories']])
        prompt_eval = f"""
            基于以下 {start_date} 到 {end_date} 的消费统计数据，请给出一份简短、专业且贴心的财务评估建议：
            - 总支出：{total_amount} 元
            - 消费构成：{categories_summary}
            请从消费结构是否合理、是否存在冲动消费风险、以及下阶段的理财建议三个角度进行分析。
            语气要像一位老朋友一样亲切。
        """
        
        response_eval = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt_eval}],
            result_format='message'
        )
        
        ai_advice = "分析完成。" 
        if response_eval.status_code == 200:
            ai_advice = response_eval.output.choices[0].message.content

        # --- 最终返回 ---
        return jsonify({
            'success': True,
            'total_amount': round(total_amount, 2),
            'category_breakdown': category_breakdown,
            'ai_advice': ai_advice
        })

    except Exception as e:
        print(f"后端错误: {e}")
        return jsonify({
            'success': False,
            'total_amount': 0,
            'category_breakdown': [],
            'ai_advice': f'处理出错: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
