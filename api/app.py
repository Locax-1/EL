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

@app.route('/api/ai-evaluate', methods=['POST'])
def ai_evaluate():
    data = request.json
    records = data.get('records', [])
    time_range = data.get('time_range', '未知时间段')

    # 1. 格式化前端传来的数据为文本
    # 这一步非常重要，要把 JSON 转成通义千问能读懂的自然语言
    record_text = ""
    for record in records:
        record_text += f"日期:{record['date']}, 类型:{record['type']}, 金额:{record['amount']}元\n"
    
    # 2. 构建 Prompt（提示词）
    # 这里的提示词决定了 AI 的回答质量
    prompt = f"""
    你是一位专业的财务分析师。请根据用户在 {time_range} 的消费记录，进行深度分析。
    要求：
    1. 计算总支出。
    2. 分析消费结构（如餐饮、交通占比）。
    3. 指出不合理的消费（如单笔过大、非必要支出）。
    4. 给出3条具体的省钱建议。
    
    消费记录如下：
    {record_text}
    """

    try:
        # 3. 调用通义千问模型
        # 这里使用 qwen-max 模型，效果较好
        response = Generation.call(
            model='qwen-max',
            prompt=prompt
        )
        
        # 4. 返回 AI 的分析结果
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'analysis': response.output.text
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AI 分析失败: ' + str(response.code)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/query-range', methods=['POST'])
def query_range():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    records = data.get('records', [])
    
    if not records:
        return jsonify({'success': False, 'error': '没有可分析的数据'})

    try:
        # 1. 构建 Prompt，让 AI 进行语义合并和分类归一化
        records_str = "\n".join([f"日期:{r['date']}, 类型:{r['type']}, 金额:{r['amount']}" for r in records])
        
        prompt = f"""
        你是一个专业的财务数据分析师。以下是用户在 {start_date} 到 {end_date} 期间的原始消费记录：
        {records_str}
        
        请帮我将这些记录进行“语义合并”和“分类归一化”。
        例如，将“午餐”、“晚餐”、“请客吃饭”、“麦当劳”统一归类为“餐饮”；将“滴滴”、“地铁”、“打车”、“公交”统一归类为“交通”；将“购物”、“淘宝”、“京东”、“拼多多”统一归类为“购物”；将“电影”、“游戏”、“旅游”统一归类为“娱乐”。

        请严格只返回一个 JSON 数组，不要包含任何其他解释文字。格式如下：
        [
            {{"type": "餐饮", "amount": 45.0}},
            {{"type": "交通", "amount": 120.0}}
        ]
        """
        
        # 2. 调用通义千问大模型
        response = Generation.call(
            model="qwen-turbo",
            messages=[{"role": "user", "content": prompt}],
            result_format='message'
        )
        
        # 3. 解析 AI 返回的内容
        ai_content = response.output.choices[0].message.content
        
        # 4. 提取 JSON 部分（容错处理）
        json_match = re.search(r'\[\s*{.*}\s*\]', ai_content, re.DOTALL)
        if not json_match:
            raise ValueError("AI 返回内容中未找到有效的 JSON 数组")
            
        normalized_records = json.loads(json_match.group(0))
        
        # 5. Python 进行精确计算
        category_stats = defaultdict(float)
        total_amount = 0.0
        
        for record in normalized_records:
            category = record.get('type', '未分类')
            amount = float(record.get('amount', 0.0))
            category_stats[category] += amount
            total_amount += amount
            
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        
        # 6. 格式化输出文本
        summary_text = f"📅 统计周期：{start_date} 至 {end_date}\n"
        summary_text += f"💰 总消费金额：¥{total_amount:.2f}\n\n"
        summary_text += "🤖 AI 智能分类明细：\n"
        for cat, amt in sorted_categories:
            percentage = (amt / total_amount * 100) if total_amount > 0 else 0
            summary_text += f"- {cat}: ¥{amt:.2f} ({percentage:.1f}%)\n"
            
        return jsonify({'success': True, 'summary': summary_text})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f"AI 分析出错: {str(e)}"})
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)