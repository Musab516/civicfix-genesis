import io, os, sqlite3, math, datetime, secrets, hashlib, hmac, time
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT=Path(__file__).resolve().parent
DB=Path(os.getenv('CIVICFIX_DB', str(ROOT/'civicfix.db')))
DB.parent.mkdir(parents=True, exist_ok=True)
app=FastAPI(title='CivicFix API',version='1.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
CATEGORIES=['Pothole','Garbage','Broken Streetlight','Water Leakage','Damaged Road','Other']
LABELS={'Pothole':'a pothole in a road','Garbage':'a pile of garbage or trash on a street','Broken Streetlight':'a broken streetlight','Water Leakage':'water leaking from a pipe onto the street','Damaged Road':'a cracked or damaged road','Other':'an unrelated photograph'}
@contextmanager
def connect():
    db=sqlite3.connect(DB);db.row_factory=sqlite3.Row
    try: yield db;db.commit()
    finally: db.close()
with connect() as db:
    db.execute('CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, description TEXT NOT NULL, location TEXT NOT NULL, lat REAL, lng REAL, status TEXT NOT NULL DEFAULT "Reported", priority TEXT NOT NULL, date TEXT NOT NULL, image BLOB, image_type TEXT)')

# Safe, additive migration: existing civicfix.db and reports remain untouched.
with connect() as db:
    cols={r['name'] for r in db.execute('PRAGMA table_info(reports)')}
    if 'user_id' not in cols: db.execute('ALTER TABLE reports ADD COLUMN user_id INTEGER')
    db.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT "citizen", created_at TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS votes(user_id INTEGER NOT NULL, report_id INTEGER NOT NULL, PRIMARY KEY(user_id,report_id))')
    cols={r['name'] for r in db.execute('PRAGMA table_info(reports)')}
    if 'severity_score' not in cols: db.execute('ALTER TABLE reports ADD COLUMN severity_score INTEGER')
    if 'severity_reason' not in cols: db.execute('ALTER TABLE reports ADD COLUMN severity_reason TEXT')
    if 'resolved_at' not in cols: db.execute('ALTER TABLE reports ADD COLUMN resolved_at TEXT')
    db.execute('CREATE TABLE IF NOT EXISTS resolution_evidence(report_id INTEGER PRIMARY KEY, image BLOB NOT NULL, image_type TEXT NOT NULL, note TEXT NOT NULL, uploaded_by INTEGER NOT NULL, created_at TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL, admin_id INTEGER NOT NULL, old_status TEXT, new_status TEXT, date TEXT NOT NULL)')

def hash_password(password):
    salt=secrets.token_bytes(16)
    key=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,240000)
    return salt.hex()+':'+key.hex()
def check_password(password,stored):
    try:
        salt,key=stored.split(':')
        return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),240000),bytes.fromhex(key))
    except (ValueError,TypeError):return False

def get_user(authorization:str|None=Header(None)):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Login required')
    token=authorization[7:]
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    with connect() as db:
        u=db.execute('SELECT users.id,users.name,users.email,users.role FROM users JOIN sessions ON users.id=sessions.user_id WHERE token_hash=? AND expires>?',(token_hash,int(time.time()))).fetchone()
    if not u:raise HTTPException(401,'Invalid or expired session')
    return dict(u)
def admin_only(user=Depends(get_user)):
    if user['role']!='admin':raise HTTPException(403,'Admin only')
    return user
class Credentials(BaseModel):
    email:str
    password:str
class Registration(Credentials):
    name:str
class Status(BaseModel):status:str

def issue_token(db,user):
    token=secrets.token_urlsafe(32)
    db.execute('INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],int(time.time())+7*86400))
    return {'token':token,'user':{k:user[k] for k in ('id','name','email','role')}}
@app.post('/api/auth/register',status_code=201)
def register(body:Registration):
    email=body.email.strip().lower();name=body.name.strip()
    if not name or len(name)>100 or len(email)>254 or '@' not in email or len(body.password)<8:raise HTTPException(400,'Provide name, valid email and password with at least 8 characters')
    with connect() as db:
        try:
            cur=db.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES (?,?,?,?,?)',(name,email,hash_password(body.password),'citizen',datetime.datetime.now(datetime.timezone.utc).isoformat()))
        except sqlite3.IntegrityError:raise HTTPException(409,'Email already registered')
        user=db.execute('SELECT id,name,email,role FROM users WHERE id=?',(cur.lastrowid,)).fetchone()
        return issue_token(db,user)
@app.post('/api/auth/login')
def login(body:Credentials):
    with connect() as db:
        user=db.execute('SELECT * FROM users WHERE email=?',(body.email.strip().lower(),)).fetchone()
        if not user or not check_password(body.password,user['password_hash']):raise HTTPException(401,'Invalid email or password')
        return issue_token(db,user)
@app.get('/api/auth/me')
def me(user=Depends(get_user)):return user
@app.post('/api/auth/logout')
def logout(authorization:str|None=Header(None),user=Depends(get_user)):
    with connect() as db:db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(authorization[7:].encode()).hexdigest(),))
    return {'ok':True}
@app.get('/api/my-reports')
def my_reports(user=Depends(get_user)):
    with connect() as db:return [public(x) for x in db.execute('SELECT * FROM reports WHERE user_id=? ORDER BY id DESC',(user['id'],))]
@app.get('/api/admin/overview')
def overview(user=Depends(admin_only)):
    with connect() as db:
        counts={r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) n FROM reports GROUP BY status')}
        return {'total':sum(counts.values()),'status_counts':counts,'users':db.execute('SELECT COUNT(*) FROM users').fetchone()[0], 'priorities':{r['priority']:r['n'] for r in db.execute('SELECT priority,COUNT(*) n FROM reports GROUP BY priority')}}
@app.post('/api/reports/{report_id}/vote')
def vote(report_id:int,user=Depends(get_user)):
    with connect() as db:
        if not db.execute('SELECT id FROM reports WHERE id=?',(report_id,)).fetchone():raise HTTPException(404,'Report not found')
        has=db.execute('SELECT 1 FROM votes WHERE user_id=? AND report_id=?',(user['id'],report_id)).fetchone()
        if has:db.execute('DELETE FROM votes WHERE user_id=? AND report_id=?',(user['id'],report_id))
        else:db.execute('INSERT INTO votes(user_id,report_id) VALUES (?,?)',(user['id'],report_id))
        return {'voted':not bool(has),'votes':db.execute('SELECT COUNT(*) FROM votes WHERE report_id=?',(report_id,)).fetchone()[0]}

def distance(a,b,c,d):
    r1,r2=math.radians(a),math.radians(c);dl=math.radians(c-a);dn=math.radians(d-b)
    h=math.sin(dl/2)**2+math.cos(r1)*math.cos(r2)*math.sin(dn/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(h)))
def public(row):
    x=dict(row);x.pop('image',None);x.pop('image_type',None);x.pop('user_id',None);x['reporter']='Anonymous resident';x['has_image']=bool(row['image']);return x

def severity(category,description,votes=0):
    # Explainable rule-based triage, not a trained severity model.
    # Operational emergency response must never depend solely on this score.
    base={'Pothole':65,'Garbage':35,'Broken Streetlight':55,'Water Leakage':70,'Damaged Road':70,'Other':25}.get(category,25)
    signals={'school':8,'hospital':10,'injury':12,'accident':12,'danger':8,'blocked':10,'flood':12,'electric':10,'children':8,'major road':8}
    found=[word for word in signals if word in description.lower()]
    score=min(100,base+sum(signals[w] for w in found)+min(votes,10)*2)
    level='Critical' if score>=85 else 'High' if score>=65 else 'Medium' if score>=40 else 'Low'
    reason='Rule-based estimate using issue type'+(', reported context: '+', '.join(found) if found else '')+(f', {votes} votes' if votes else '')
    return level,score,reason


@app.get('/api/health')
def health():return {'ok':True,'classifier':'optional CLIP zero-shot model'}
@app.get('/api/reports')
def list_reports():
    with connect() as db:
        items=[]
        for r in db.execute('SELECT * FROM reports ORDER BY id').fetchall():
            votes=db.execute('SELECT COUNT(*) FROM votes WHERE report_id=?',(r['id'],)).fetchone()[0]
            level,score,reason=severity(r['category'],r['description'],votes)
            evidence=db.execute('SELECT 1 FROM resolution_evidence WHERE report_id=?',(r['id'],)).fetchone()
            items.append(dict(public(r),votes=votes,priority=level,severity_score=score,severity_reason=reason,has_resolution_photo=bool(evidence)))
        return items
@app.get('/api/reports/{report_id}/image')
def get_image(report_id:int):
    from fastapi.responses import Response
    with connect() as db:r=db.execute('SELECT image,image_type FROM reports WHERE id=?',(report_id,)).fetchone()
    if not r or not r['image']:raise HTTPException(404,'No image')
    return Response(r['image'],media_type=r['image_type'])
@app.get('/api/duplicates')
def duplicates(category:str,lat:float,lng:float):
    with connect() as db:rows=db.execute('SELECT * FROM reports WHERE category=? AND status != "Resolved" AND lat IS NOT NULL AND lng IS NOT NULL',(category,)).fetchall()
    return {'matches':[public(r) for r in rows if distance(lat,lng,r['lat'],r['lng'])<=200]}
@app.post('/api/reports',status_code=201)
async def create_report(category:str=Form(...),description:str=Form(...),location:str=Form(...),lat:float|None=Form(None),lng:float|None=Form(None),image:UploadFile|None=File(None),user=Depends(get_user)):
    if category not in CATEGORIES:raise HTTPException(400,'Invalid category')
    if not description.strip() or not location.strip():raise HTTPException(400,'Description and location required')
    if lat is not None and not -90<=lat<=90 or lng is not None and not -180<=lng<=180:raise HTTPException(400,'Invalid GPS')
    data=None;mime=None
    if image and image.filename:
        mime=image.content_type
        if mime not in ['image/jpeg','image/png','image/webp']:raise HTTPException(400,'Use JPEG, PNG or WebP')
        data=await image.read(5*1024*1024+1)
        if len(data)>5*1024*1024:raise HTTPException(413,'Image exceeds 5 MB')
        from PIL import Image
        try:
            im=Image.open(io.BytesIO(data));im.verify()
        except Exception:raise HTTPException(400,'Invalid image file')
    priority,score,reason=severity(category,description)
    with connect() as db:
        cur=db.execute('INSERT INTO reports(category,description,location,lat,lng,status,priority,date,image,image_type,user_id,severity_score,severity_reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(category,description.strip(),location.strip(),lat,lng,'Reported',priority,datetime.date.today().isoformat(),data,mime,user['id'],score,reason))
        row=db.execute('SELECT * FROM reports WHERE id=?',(cur.lastrowid,)).fetchone()
    return public(row)
@app.patch('/api/reports/{report_id}')
def update(report_id:int,body:Status,user=Depends(admin_only)):
    if body.status not in ('Reported','In Progress','Resolved'):raise HTTPException(400,'Invalid status')
    with connect() as db:
        before=db.execute('SELECT status FROM reports WHERE id=?',(report_id,)).fetchone()
        cur=db.execute("UPDATE reports SET status=?,resolved_at=CASE WHEN ? = 'Resolved' THEN COALESCE(resolved_at,?) ELSE NULL END WHERE id=?",(body.status,body.status,datetime.datetime.now(datetime.timezone.utc).isoformat(),report_id))
        if before:db.execute('INSERT INTO audit_log(report_id,admin_id,old_status,new_status,date) VALUES(?,?,?,?,?)',(report_id,user['id'],before['status'],body.status,datetime.datetime.now(datetime.timezone.utc).isoformat()))
        if not cur.rowcount:raise HTTPException(404,'Report not found')
        row=db.execute('SELECT * FROM reports WHERE id=?',(report_id,)).fetchone()
    return public(row)

@app.get('/api/admin/analytics')
def analytics(user=Depends(admin_only)):
    with connect() as db:
        records=db.execute('SELECT id,category,status,lat,lng,date,resolved_at FROM reports').fetchall()
        return {
            'category_counts':{r['category']:r['n'] for r in db.execute('SELECT category,COUNT(*) n FROM reports GROUP BY category')},
            'status_counts':{r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) n FROM reports GROUP BY status')},
            'daily_counts':[dict(x) for x in db.execute('SELECT date,COUNT(*) count FROM reports GROUP BY date ORDER BY date DESC LIMIT 14')],
            'hotspots':[{'lat':r['lat'],'lng':r['lng'],'category':r['category'],'status':r['status']} for r in records if r['lat'] is not None and r['lng'] is not None],
            'resolved_count':sum(r['status']=='Resolved' for r in records),
            'total':len(records),
            'resolution_rate':round(100*sum(r['status']=='Resolved' for r in records)/len(records),1) if records else 0,
            'note':'Hotspots are reported coordinates, not predictions. Small datasets are not representative.'
        }

@app.get('/api/reports/{report_id}/resolution')
def resolution_photo(report_id:int):
    from fastapi.responses import Response
    with connect() as db:r=db.execute('SELECT image,image_type FROM resolution_evidence WHERE report_id=?',(report_id,)).fetchone()
    if not r:raise HTTPException(404,'No resolution evidence')
    return Response(r['image'],media_type=r['image_type'],headers={'Cache-Control':'no-store'})

@app.post('/api/admin/reports/{report_id}/resolution')
async def upload_resolution(report_id:int,image:UploadFile=File(...),note:str=Form(''),user=Depends(admin_only)):
    if image.content_type not in ('image/jpeg','image/png','image/webp'):raise HTTPException(400,'Use JPEG, PNG or WebP')
    data=await image.read(5*1024*1024+1)
    if len(data)>5*1024*1024:raise HTTPException(413,'Image exceeds 5 MB')
    from PIL import Image
    try:
        im=Image.open(io.BytesIO(data));im.verify()
    except Exception:raise HTTPException(400,'Invalid image')
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with connect() as db:
        report=db.execute('SELECT status FROM reports WHERE id=?',(report_id,)).fetchone()
        if not report:raise HTTPException(404,'Report not found')
        db.execute('INSERT INTO resolution_evidence(report_id,image,image_type,note,uploaded_by,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(report_id) DO UPDATE SET image=excluded.image,image_type=excluded.image_type,note=excluded.note,uploaded_by=excluded.uploaded_by,created_at=excluded.created_at',(report_id,data,image.content_type,note[:500],user['id'],now))
        db.execute('UPDATE reports SET status=?,resolved_at=COALESCE(resolved_at,?) WHERE id=?',('Resolved',now,report_id))
        db.execute('INSERT INTO audit_log(report_id,admin_id,old_status,new_status,date) VALUES(?,?,?,?,?)',(report_id,user['id'],report['status'],'Resolved',now))
    return {'ok':True,'report_id':report_id,'status':'Resolved','has_resolution_photo':True}

_classifier=None
@app.post('/api/classify')
async def classify(image:UploadFile=File(...)):
    if os.getenv('CIVICFIX_LOCAL_AI') != '1':
        raise HTTPException(503, 'Server AI disabled; use the browser-based classifier.')
    global _classifier
    if image.content_type not in ('image/jpeg','image/png','image/webp'):raise HTTPException(400,'Invalid image type')
    data=await image.read(5*1024*1024+1)
    if len(data)>5*1024*1024:raise HTTPException(413,'Image exceeds 5 MB')
    from PIL import Image
    try: im=Image.open(io.BytesIO(data)).convert('RGB')
    except Exception:raise HTTPException(400,'Invalid image')
    try:
        if _classifier is None:
            from transformers import pipeline
            _classifier=pipeline('zero-shot-image-classification',model='openai/clip-vit-base-patch32')
        results=_classifier(im,candidate_labels=list(LABELS.values()))
    except (ImportError,OSError,RuntimeError) as e:
        raise HTTPException(503,'AI model unavailable. Install requirements-ai.txt and allow model download, or select a category manually.') from e
    scores={next(k for k,v in LABELS.items() if v==r['label']):round(r['score'],3) for r in results}
    best=max(scores,key=scores.get)
    return {'category':best,'confidence':scores[best],'scores':scores,'note':'AI suggestion only; verify before submitting.'}
app.mount('/',StaticFiles(directory=ROOT,html=True),name='frontend')

if __name__=='__main__':
    import getpass, sys
    if len(sys.argv)==2 and sys.argv[1]=='create-admin':
        email=input('Admin email: ').strip().lower();name=input('Admin name: ').strip();password=getpass.getpass('Admin password (min 8 chars): ')
        if not name or '@' not in email or len(password)<8:sys.exit('Invalid name, email or password')
        with connect() as db:
            if db.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone():sys.exit('Email already exists; choose another email')
            db.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES (?,?,?,?,?)',(name,email,hash_password(password),'admin',datetime.datetime.now(datetime.timezone.utc).isoformat()))
        print('Admin created successfully')
    else:print('Usage: python backend.py create-admin')
