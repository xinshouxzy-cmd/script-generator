"""AI脚本生成器 — Flask主应用"""
import os
import json
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from qa_engine import create_session, get_session, load_knowledge
from template_store import store
from coze_client import generate_script
import json

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


@app.route("/api/templates/push", methods=["POST"])
def push_templates():
    ok = store.push_to_github()
    return jsonify({"success": ok})


@app.route("/api/knowledge", methods=["GET"])
def get_knowledge():
    kb = load_knowledge()
    return jsonify(kb.get("knowledge_base", kb))


@app.route("/api/knowledge", methods=["POST"])
def save_knowledge():
    data = request.get_json()
    try:
        kb_file = os.path.join(os.path.dirname(__file__), "data", "knowledge.json")
        wrapped = {"knowledge_base": data}
        with open(kb_file, "w", encoding="utf-8") as f:
            json.dump(wrapped, f, ensure_ascii=False, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


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
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:20px;max-width:900px;margin:0 auto}
h1{font-size:20px;margin-bottom:8px;background:linear-gradient(135deg,#fe2c55,#ff9a44);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
h2{font-size:16px;margin:24px 0 12px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px}
th,td{padding:10px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.08)}
th{color:rgba(255,255,255,0.5);font-weight:500}
.tag{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;margin-right:4px}
.tag-type{background:rgba(37,244,238,0.12);color:#25f4ee}.tag-scene{background:rgba(254,44,85,0.1);color:#fe2c55}.tag-source{background:rgba(255,154,68,0.1);color:#ff9a44}
.btn-sm{padding:6px 14px;border:none;border-radius:6px;font-size:12px;cursor:pointer;margin:2px;color:#fff}
.btn-danger{background:rgba(254,44,85,0.5)}.btn-success{background:rgba(37,244,238,0.3)}.btn-blue{background:rgba(24,95,165,0.5)}
.form-box{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:16px;margin-bottom:16px}
.form-box input,.form-box textarea,.form-box select{width:100%;padding:10px;margin:6px 0;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:8px;color:#fff;font-size:13px;font-family:inherit}
.form-box textarea{resize:vertical;min-height:60px}
.form-row{display:flex;gap:10px}
.form-row>*{flex:1}
.loading{text-align:center;padding:20px;color:rgba(255,255,255,0.4)}
.green{color:#25f4ee}</style>
</head>
<body>
<h1>📝 脚本生成器 — 管理后台</h1>
<p style="color:rgba(255,255,255,0.4);font-size:13px">三大体系：知识库 · 合规规则 · 模板库</p>

<div style="margin:16px 0;display:flex;gap:8px;flex-wrap:wrap">
<button class="btn-sm btn-success" onclick="syncGitHub()">🔄 同步GitHub</button>
<button class="btn-sm btn-success" onclick="pushGitHub()">📤 推送到GitHub</button>
<button class="btn-sm btn-blue" onclick="showAddForm()">+ 添加模板</button>
</div>

<h2>银行业务知识库 <span style="font-size:12px;color:rgba(255,255,255,0.4)">影响脚本内容准确性</span></h2>
<div id="kbArea"><div class="loading">加载中...</div></div>

<h2>合规规则 <span style="font-size:12px;color:rgba(255,255,255,0.4)">每个脚本必须遵守</span></h2>
<div id="rulesArea"><div class="loading">加载中...</div></div>

<h2>模板列表 <span style="font-size:12px;color:rgba(255,255,255,0.4)" id="tplCount"></span></h2>
<div id="tableArea"><div class="loading">加载中...</div></div>

<div id="editForm" style="display:none"></div>

<script>
var allTemplates=[];
function load(){
    document.getElementById('tableArea').innerHTML='<div class="loading">加载中...</div>';
    fetch('/api/templates').then(r=>r.json()).then(ts=>{
        allTemplates=ts;
        document.getElementById('tplCount').textContent='共'+ts.length+'条';
        if(!ts.length){document.getElementById('tableArea').innerHTML='<p style="color:rgba(255,255,255,0.4)">暂无模板，点击上方按钮添加</p>';return}
        var rows=ts.map(function(t){
            return '<tr><td><strong>'+t.title+'</strong><br><span style="font-size:11px;color:rgba(255,255,255,0.4)">'+t.script_structure+'</span></td><td><span class="tag tag-type">'+t.type+'</span><span class="tag tag-scene">'+t.scene+'</span></td><td><span class="tag tag-source">'+t.source+'</span></td><td>'+t.created_at+'</td><td><button class="btn-sm" style="background:rgba(37,244,238,0.2)" onclick="editTpl(\''+t.id+'\')">编辑</button><button class="btn-sm btn-danger" onclick="del(\''+t.id+'\')">删除</button></td></tr>';
        }).join('');
        document.getElementById('tableArea').innerHTML='<table><thead><tr><th>模板名称</th><th>分类</th><th>来源</th><th>时间</th><th>操作</th></tr></thead><tbody>'+rows+'</tbody></table>';
    });
}
function syncGitHub(){
    fetch('/api/templates/refresh',{method:'POST'}).then(r=>r.json()).then(function(d){
        alert(d.success?'同步成功，共'+d.count+'条模板':'同步失败');
        load();
    });
}
function pushGitHub(){
    fetch('/api/templates/push',{method:'POST'}).then(r=>r.json()).then(function(d){
        alert(d.success?'推送成功':'推送失败');
    });
}
function showAddForm(){
    var h='<div class="form-box"><h2>添加新模板</h2>';
    h+='<div class="form-row"><input id="af_title" placeholder="模板名称"><input id="af_scene" placeholder="场景（如存款、反诈）"></div>';
    h+='<select id="af_type"><option>产品营销</option><option>金融科普</option><option>政策解读</option><option>企业文化</option></select>';
    h+='<input id="af_structure" placeholder="脚本结构（如：痛点引入→产品介绍→对比优势→行动号召）">';
    h+='<textarea id="af_shots" placeholder="分镜提示（每行一个）"></textarea>';
    h+='<textarea id="af_sample" placeholder="样例开头"></textarea>';
    h+='<input id="af_tags" placeholder="热门标签（逗号分隔）">';
    h+='<div style="margin-top:8px"><button class="btn-sm btn-success" onclick="saveTpl()">保存模板</button><button class="btn-sm btn-danger" onclick="document.getElementById(\'editForm\').style.display=\'none\'">取消</button></div></div>';
    document.getElementById('editForm').innerHTML=h;
    document.getElementById('editForm').style.display='block';
    document.getElementById('editForm').scrollIntoView({behavior:'smooth'});
}
function editTpl(id){
    var t=allTemplates.find(function(x){return x.id===id});if(!t)return;
    var h='<div class="form-box"><h2>编辑模板：'+t.title+'</h2>';
    h+='<div class="form-row"><input id="af_title" value="'+t.title+'"><input id="af_scene" value="'+t.scene+'"></div>';
    h+='<select id="af_type">'+['产品营销','金融科普','政策解读','企业文化'].map(function(o){return '<option'+(o===t.type?' selected':'')+'>'+o+'</option>';}).join('')+'</select>';
    h+='<input id="af_structure" value="'+(t.script_structure||'')+'">';
    h+='<textarea id="af_shots">'+(t.shot_tips||[]).join('\n')+'</textarea>';
    h+='<textarea id="af_sample">'+(t.sample||'')+'</textarea>';
    h+='<input id="af_tags" value="'+(t.hot_tags||[]).join(',')+'">';
    h+='<div style="margin-top:8px"><input type="hidden" id="af_id" value="'+t.id+'"><button class="btn-sm btn-success" onclick="saveTpl(true)">更新模板</button><button class="btn-sm btn-danger" onclick="document.getElementById(\'editForm\').style.display=\'none\'">取消</button></div></div>';
    document.getElementById('editForm').innerHTML=h;
    document.getElementById('editForm').style.display='block';
    document.getElementById('editForm').scrollIntoView({behavior:'smooth'});
}
function saveTpl(isUpdate){
    var id=document.getElementById('af_id');var tid=id?encodeURIComponent(id.value):'';
    var data={
        type:document.getElementById('af_type').value,
        scene:document.getElementById('af_scene').value,
        title:document.getElementById('af_title').value,
        script_structure:document.getElementById('af_structure').value,
        shot_tips:document.getElementById('af_shots').value.split('\n').filter(Boolean),
        sample:document.getElementById('af_sample').value,
        hot_tags:document.getElementById('af_tags').value.split(',').map(function(s){return s.trim();}).filter(Boolean),
        source:'manual'
    };
    var method=isUpdate?'PUT':'POST';
    var url='/api/templates'+(isUpdate?'/'+tid:'');
    fetch(url,{method:method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>r.json()).then(function(){
        pushGitHub();
        document.getElementById('editForm').style.display='none';
        load();
    });
}
function del(id){if(confirm('确认删除？')){fetch('/api/templates/'+id,{method:'DELETE'}).then(function(){pushGitHub();load();});}}
function loadKB(){
    document.getElementById('kbArea').innerHTML='<div class="loading">加载中...</div>';
    document.getElementById('rulesArea').innerHTML='<div class="loading">加载中...</div>';
    fetch('/api/knowledge').then(r=>r.json()).then(function(d){
        var prods=d.banking_products||[];
        var kbhtml='<div class="form-box"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><strong>产品分类</strong><button class="btn-sm" style="background:rgba(37,244,238,0.3)" onclick="addKB()">+ 添加分类</button></div>';
        prods.forEach(function(c,i){
            kbhtml+='<div style="margin:4px 0;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px"><strong>'+c.category+'</strong><br><span style="font-size:12px;color:rgba(255,255,255,0.5)">'+c.items.join('、')+'</span> <button class="btn-sm btn-danger" style="font-size:10px;padding:2px 8px" onclick="delKB('+i+')">删除</button></div>';
        });
        kbhtml+='</div>';
        document.getElementById('kbArea').innerHTML=kbhtml||'暂无';

        var rules=d.compliance_rules||[];
        var rh='<div class="form-box"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><strong>合规规则</strong><button class="btn-sm" style="background:rgba(37,244,238,0.3)" onclick="addRule()">+ 添加规则</button></div>';
        rules.forEach(function(r,i){
            rh+='<div style="padding:6px 0;display:flex;justify-content:space-between"><span>✅ '+r+'</span><button class="btn-sm btn-danger" style="font-size:10px;padding:2px 8px" onclick="delRule('+i+')">删除</button></div>';
        });
        rh+='</div>';
        document.getElementById('rulesArea').innerHTML=rh||'暂无';
        allKB=d;
    });
}
function addKB(){
    var cat=prompt('分类名称（如：存款、贷款、理财）');if(!cat)return;
    var items=prompt('包含的产品（逗号分隔）');if(!items)return;
    allKB.banking_products.push({category:cat,items:items.split(',').map(function(s){return s.trim()})});
    saveKB();
}
function delKB(i){if(confirm('确认删除此分类？')){allKB.banking_products.splice(i,1);saveKB();}}
function addRule(){
    var r=prompt('输入合规规则（如：必须标注风险提示）');if(!r)return;
    allKB.compliance_rules.push(r);
    saveKB();
}
function delRule(i){if(confirm('确认删除此规则？')){allKB.compliance_rules.splice(i,1);saveKB();}}
var allKB={};
function saveKB(){
    fetch('/api/knowledge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(allKB)}).then(function(r){return r.json()}).then(function(d){
        if(d.success){loadKB();pushGitHub();}else{alert('保存失败: '+d.error)}
    });
}
loadKB();load();
</script>
</body>
</html>'''


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=False)
