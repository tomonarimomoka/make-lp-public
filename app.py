# app.py
import random
import string
import os
import re

from flask import Flask, request, redirect ,render_template
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('OPENAI_API_KEY')
HTML_FOLDER = './html/'

# キーは環境変数に設定
client = OpenAI(
   api_key=key
)

app = Flask(__name__,static_folder='html')

def extract_html_content(text):
    new_string = text.replace("```html", "")
    new_string = new_string.replace("```", "")
    return new_string

def addCondition(prompt,conditonType,condition):
    if(len(condition) != 0):
        prompt += "\n" + "・"
        if (len(conditonType) != 0):
            prompt += str(conditonType) + "は" + str(condition)
        else:
            prompt += condition    
    return prompt

def makePromptForCatchcopy(businessType,target,personasGender,age,imageColor,detail):
    prompt = "以下の特徴をもつビジネスのキャッチコピーを考えてください。"
    addCondition(prompt,"業界",businessType)
    prompt = addCondition(prompt,"ターゲット",target)
    prompt = addCondition(prompt,"ペルソナの性別",personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢",age)
    prompt = addCondition(prompt,"LPのイメージカラー",imageColor)
    prompt = addCondition(prompt,"",detail)
    
    return prompt

def makepromptForSalesPoint(businessType, target, personasGender, age, imageColor, detail, catchcopy):    
    prompt = "以下の特徴をもつランディングページに記載するセールスポイントを3つ考えてください。"
    addCondition(prompt,"業界", businessType)
    prompt = addCondition(prompt,"ターゲット", target)
    prompt = addCondition(prompt,"ペルソナの性別", personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢", age)
    prompt = addCondition(prompt,"LPのイメージカラー", imageColor)
    prompt = addCondition(prompt,"キャッチコピー", catchcopy)
    prompt = addCondition(prompt,"サービス概要", detail)
    prompt += "その際、返答の形式は「1.」「2.」「3.」で並べる形でお願いします。"

    return prompt

def makepromptForLP(referenceUrl,businessType,target,personasGender,age,imageColor,detail,catchcopy,sales_points):    
    prompt = "以下の特徴をもつランディングページのHTMLを作成してください。\n"
    addCondition(prompt,"業界",businessType)
    prompt = addCondition(prompt,"ターゲット",target)
    prompt = addCondition(prompt,"ペルソナの性別",personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢",age)
    prompt = addCondition(prompt,"LPのイメージカラー",imageColor)
    prompt = addCondition(prompt,"キャッチコピー",catchcopy)
    prompt = addCondition(prompt,"サービス概要",detail)
    for index, point in enumerate(sales_points):
        prompt = addCondition(prompt, "セールスポイント" + str(index), point)

    prompt += "・キャッチコピーはh1タグを使うこと\n"
    prompt += "・セールスポイントの内容はページ内で必ず3つ記載し横並びのデザインにすること\n" 
    prompt += "・背景色と文字の色が似すぎていると文字が見えなくなるので、文字が識別できる範囲でイメージに沿った色にすること\n"
    prompt += "・背景色はグラデーションにすること\n"
    prompt += "・レスポンシブデザインにすること\n"
    prompt += "・回答はHTML部分を返答すること\n"
    prompt += "・下記ページを参照すること\n"
    prompt += referenceUrl
    
    return prompt

def split_by_delimiters(input_string):
    # 正規表現パターンを定義して、「1.」、「2.」、「3.」のような形式をマッチさせる
    pattern = r'\d+\.'  # 区切り文字をキャプチャしない
    # パターンに基づいて分割
    parts = re.split(pattern, input_string)
    # 最初の要素は空文字になるため、削除
    if parts[0] == '':
        parts = parts[1:]
    return parts

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/lp')
def lp():
    return render_template('lp.html')


@app.route('/html/<filename>', methods=['GET'])
def htmlimage(filename):
    return app.send_static_file(filename)

def openai_llm(question, context):
    messages = [
        {"role": "system", "content": question},
        {"role": "user", "content": context},
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    response_message = response.choices[0].message.content
    return response_message

def generate_random_filename(length=10, extension=None):
    # 使用する文字のセットを定義
    characters = string.ascii_letters + string.digits
    # 指定された長さのランダムな文字列を生成
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    if extension:
        # 拡張子の先頭にドットがない場合は追加
        if not extension.startswith('.'):
            extension = '.' + extension
        return random_string + extension
    else:
        return random_string


@app.route('/submit', methods=['POST'])
def submit():
    industry = request.form['industry']
    target = request.form['target']
    gender = request.form['gender']
    color = request.form['color']
    age = request.form['age']
    url = request.form['url']
    detail = request.form['detail']
    
    #キャッチコピーを考えさせる
    context = makePromptForCatchcopy(industry,target,gender,age,color,detail)
    catchcopy = openai_llm("あなたはプロのライターです。", context)

    #セールスポイント作成
    context = makepromptForSalesPoint(industry,target,gender,age,color,detail,catchcopy)
    sales_points_res = openai_llm("あなたはプロのライターです。", context)
    sales_points = split_by_delimiters(sales_points_res)

    #画像生成
    # generate_hero_image(industry,target,gender,age,color,detail,catchcopy)

    #HTMLを生成させる
    context = makepromptForLP(url, industry,target,gender,age,color,detail,catchcopy,sales_points)
    response_message = openai_llm("あなたはプロのwebデザイナーです。", context)

    #return catchcopy + '\n' + response_message

    filename = HTML_FOLDER + generate_random_filename(10,"html")
    with open(filename, 'w', encoding='utf-8') as f:
        html_text = extract_html_content(response_message)
        f.write(html_text)
    
    return redirect(filename)

if __name__ == '__main__':
    app.run(debug=True)


