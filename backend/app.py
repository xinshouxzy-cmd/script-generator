"""AI脚本生成器 — Flask主应用"""
import os
import json
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from qa_engine import create_session, get_session
from template_store import store
from coze_client import generate_script

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template_string(EMPLOYEE_HTML)


@app.route("/admin")
def admin():
    return render_template_string(ADMIN_HTML)


@app.route("/api/qa/start", methods=["POST"])
def qa_start():
    sid, session = create_session()
    q = session.next_question()
    return jsonify({"session_id": sid, "question": q})


@app.route("/api/qa/answer", methods=["POST"])
def qa_answer():
    data = request.get_json()
    sid = data.get("session_id", "")
    answer = data.get("answer", "")
    session = get_session(sid)
    if not session:
        return jsonify({"error": "会话已过期，请重新开始"}), 400

    next_q = session.answer(answer)

    if session.is_complete():
        templates = store.get_all()
        prompt = session.build_prompt(templates)

        result = generate_script(prompt)
        if result.get("success"):
            return jsonify({"done": True, "script": result["script"]})
        else:
            err = result.get("error", "未知错误")
            raw = result.get("raw", "")
            return jsonify({"done": True, "script": prompt, "note": f"Bot调用失败: {err}", "raw": raw})
    
    return jsonify({"done": False, "question": next_q})


@app.route("/api/templates", methods=["GET"])
def list_templates():
    return jsonify(store.get_all())


@app.route("/api/templates", methods=["POST"])
def add_template():
    data = request.get_json()
    t = store.add(data)
    store.push_to_github()
    return jsonify(t)


@app.route("/api/templates/<tid>", methods=["PUT"])
def update_template(tid):
    data = request.get_json()
    t = store.update(tid, data)
    if t:
        store.push_to_github()
    return jsonify(t or {"error": "not found"})


@app.route("/api/templates/<tid>", methods=["DELETE"])
def delete_template(tid):
    ok = store.delete(tid)
    if ok:
        store.push_to_github()
    return jsonify({"success": ok})


@app.route("/api/templates/refresh", methods=["POST"])
def refresh_templates():
    ok = store.refresh_from_github()
    return jsonify({"success": ok, "count": len(store.get_all())})


EMPLOYEE_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>AI脚本生成器</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0a0a0a;min-height:100vh;display:flex;align-items:center;justify-content:center;color:#e0e0e0}
.container{width:100%;max-width:500px;padding:16px}
.card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:24px 20px}
.logo{text-align:center;margin-bottom:20px}
.logo-icon{font-size:42px}
.logo h1{font-size:20px;font-weight:700;background:linear-gradient(135deg,#fe2c55,#ff9a44);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-top:8px}
.subtitle{font-size:13px;color:rgba(255,255,255,0.4);margin-top:4px}
.chat-area{min-height:200px;max-height:400px;overflow-y:auto;margin-bottom:16px}
.question-box{background:rgba(37,244,238,0.08);border:1px solid rgba(37,244,238,0.2);border-radius:12px;padding:14px;margin-bottom:12px}
.question-box .q{font-size:14px;color:#25f4ee;margin-bottom:4px}
.question-box .q-hint{font-size:12px;color:rgba(255,255,255,0.4)}
.answer-box{background:rgba(254,44,85,0.08);border:1px solid rgba(254,44,85,0.2);border-radius:12px;padding:10px 14px;margin-bottom:12px;text-align:right;font-size:14px;color:#fe2c55}
.options-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.opt-btn{padding:10px 16px;border:1px solid rgba(37,244,238,0.3);border-radius:10px;background:rgba(37,244,238,0.06);color:#25f4ee;font-size:14px;cursor:pointer;transition:all .2s}
.opt-btn:active{background:rgba(37,244,238,0.2)}
.input-row{display:flex;gap:8px;margin-top:12px}
.input-row input{flex:1;padding:10px 14px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:10px;color:#fff;font-size:14px;outline:none;font-family:inherit}
.input-row input:focus{border-color:#fe2c55}
.btn{padding:10px 20px;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;background:linear-gradient(135deg,#fe2c55,#ff6b81);color:#fff;white-space:nowrap}
.btn:disabled{opacity:.5}
.script-output{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:16px;white-space:pre-wrap;font-size:13px;line-height:1.6;color:#e0e0e0;margin-top:12px;max-height:300px;overflow-y:auto}
.btn-copy{margin-top:12px;width:100%;padding:12px;border:none;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer;background:linear-gradient(135deg,#25f4ee,#00d4ff);color:#000}
.footer{text-align:center;margin-top:20px;font-size:12px;color:rgba(255,255,255,0.2)}
.spinner{width:28px;height:28px;border:3px solid rgba(255,255,255,0.1);border-top-color:#fe2c55;border-radius:50%;animation:spin .6s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading{text-align:center;padding:20px;color:rgba(255,255,255,0.4)}
</style>
</head>
<body>
<div class="container">
<div class="card">
<div class="logo"><div class="logo-icon">📝</div><h1>AI脚本生成器</h1><p class="subtitle">遵义农信 · 智能创作助手</p></div>
<div id="chatArea" class="chat-area"></div>
<div id="inputArea" style="display:none"></div>
<div id="btnArea"><button class="btn" onclick="startQA()" style="width:100%;padding:14px">开始创作脚本</button></div>
</div>
<div class="footer">遵义农商银行</div>
</div>
<script>
var sessionId = '', step = 0;

function appendBubble(role, text, css){
    var d=document.createElement('div');d.className=css;d.style.whiteSpace='pre-wrap';d.textContent=text;document.getElementById('chatArea').appendChild(d);d.scrollIntoView({behavior:'smooth'});
}

function startQA(){
    document.getElementById('btnArea').innerHTML='<div class="loading"><div class="spinner"></div><div>正在连接...</div></div>';
    fetch('/api/qa/start',{method:'POST'}).then(r=>r.json()).then(d=>{
        sessionId=d.session_id;
        document.getElementById('btnArea').style.display='none';
        showQuestion(d.question);
    });
}

function showQuestion(q){
    step=q.step;
    var txt=q.question;if(q.hint)txt+='\n「'+q.hint+'」';
    appendBubble('AI',txt,'question-box');
    var ia=document.getElementById('inputArea');
    ia.style.display='block';
    ia.innerHTML='<div class="input-row"><textarea id="txtInput" placeholder="输入你的想法..." rows="3" style="flex:1;padding:12px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:12px;color:#fff;font-size:14px;outline:none;font-family:inherit;resize:none;line-height:1.5"></textarea></div><button class="btn" onclick="submitAnswer(document.getElementById(\'txtInput\').value)" style="width:100%;margin-top:8px;padding:12px">确认，继续</button>';
    setTimeout(function(){var t=document.getElementById('txtInput');if(t)t.focus();},100);
}

function submitAnswer(val){
    if(!val||!val.trim())return;
    var ia=document.getElementById('inputArea');ia.innerHTML='<div class="loading"><div class="spinner"></div></div>';
    appendBubble('你',val,'answer-box');
    fetch('/api/qa/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,answer:val})}).then(r=>r.json()).then(d=>{
        document.getElementById('inputArea').innerHTML='';
        if(d.done){
            var s=d.script||'生成中...';
            document.getElementById('btnArea').style.display='block';
            document.getElementById('btnArea').innerHTML='<div class="script-output" id="scriptBox">'+s+'</div><button class="btn-copy" onclick="copyScript()">复制脚本</button><button class="btn" onclick="startQA()" style="width:100%;margin-top:8px">重新创作</button>';
            document.getElementById('chatArea').style.display='none';
        }else{
            showQuestion(d.question);
        }
    });
}

function copyScript(){
    var t=document.getElementById('scriptBox').textContent;
    navigator.clipboard.writeText(t).then(function(){alert('已复制！');});
}
</script>
</body>
</html>'''


ADMIN_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>脚本生成器 — 管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:20px;max-width:800px;margin:0 auto}
h1{font-size:20px;margin-bottom:8px;background:linear-gradient(135deg,#fe2c55,#ff9a44);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
h2{font-size:16px;margin:24px 0 12px;color:#fff}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.08)}
th{color:rgba(255,255,255,0.5);font-weight:500}
.tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;margin-right:4px}
.tag-type{background:rgba(37,244,238,0.12);color:#25f4ee}
.tag-scene{background:rgba(254,44,85,0.1);color:#fe2c55}
.tag-source{background:rgba(255,154,68,0.1);color:#ff9a44}
.btn-sm{padding:6px 12px;border:none;border-radius:6px;font-size:12px;cursor:pointer;margin-right:4px}
.btn-danger{background:rgba(254,44,85,0.15);color:#fe2c55}
.btn-success{background:rgba(37,244,238,0.15);color:#25f4ee}
.btn-amber{background:rgba(255,154,68,0.15);color:#ff9a44}
.loading{text-align:center;padding:20px;color:rgba(255,255,255,0.4)}
</style>
</head>
<body>
<h1>📝 脚本生成器 — 管理后台</h1>
<p style="color:rgba(255,255,255,0.4);font-size:13px;margin-bottom:20px">模板库管理 · 手动编辑 + 自动刷新</p>
<div style="margin-bottom:16px">
<button class="btn-sm btn-success" onclick="refreshTemplates()">🔄 从GitHub同步</button>
<button class="btn-sm btn-amber" onclick="autoRefresh()">🤖 自动抓取新模板</button>
</div>
<div id="tableArea"><div class="loading">加载中...</div></div>
<script>
function load(){
    document.getElementById('tableArea').innerHTML='<div class="loading">加载中...</div>';
    fetch('/api/templates').then(r=>r.json()).then(ts=>{
        if(!ts.length){document.getElementById('tableArea').innerHTML='<p style="color:rgba(255,255,255,0.4)">暂无模板</p>';return}
        var rows=ts.map(function(t,i){
            return '<tr><td>'+t.title+'</td><td><span class="tag tag-type">'+t.type+'</span> <span class="tag tag-scene">'+t.scene+'</span></td><td><span class="tag tag-source">'+t.source+'</span></td><td>'+t.created_at+'</td><td><button class="btn-sm btn-danger" onclick="del(\''+t.id+'\')">删除</button></td></tr>';
        }).join('');
        document.getElementById('tableArea').innerHTML='<table><thead><tr><th>模板名称</th><th>分类</th><th>来源</th><th>更新时间</th><th>操作</th></tr></thead><tbody>'+rows+'</tbody></table>';
    });
}
function refreshTemplates(){
    fetch('/api/templates/refresh',{method:'POST'}).then(r=>r.json()).then(function(d){
        alert(d.success?'已同步，共'+d.count+'条模板':'同步失败');
        load();
    });
}
function autoRefresh(){alert('自动抓取功能开发中，请手动添加模板。');}
function del(id){if(confirm('确认删除？')){fetch('/api/templates/'+id,{method:'DELETE'}).then(function(){load();});}}
load();
</script>
</body>
</html>'''


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=False)
