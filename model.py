from flask import Flask
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import json

class MyEncoder(json.JSONEncoder):
  def default(self, obj):
      if isinstance(obj, datetime):
          return obj.strftime('%Y-%m-%d %H:%M:%S')
      elif isinstance(obj, date):
          return obj.strftime('%Y-%m-%d')
      else:
          return json.JSONEncoder.default(self, obj)

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:chinatt_1347@localhost:3306/thumbops'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True
app.config['USERNAME']="admin"
app.config['PASSWORD']="admin888"
app.config['SUPERPASSWORD']="1cfaed75dcb7cca2c94c5031ce05eb88"
app.config['SECRET_KEY'] = 'jjskdjlkasjdlfjalk'

db = SQLAlchemy(app)
manager = Manager(app)

class tasklist(db.Model):
    __tablename__ = 'tasklist'
    id = db.Column(db.Integer, primary_key=True)
    taskid = db.Column(db.String(100), unique=True)
    processesnum = db.Column(db.Integer)
    title = db.Column(db.Text(86400))
    wburl = db.Column(db.String(3000))
    upnum=db.Column(db.Integer)
    percent = db.Column(db.String(320),nullable=True)
    status = db.Column(db.Integer,server_default="0")
    create_time = db.Column(db.DateTime, nullable=True)
    def __repr__(self):
        return json.dumps({"id":self.id,"processesnum":self.processesnum,"wburl":self.wburl,"upnum":self.upnum,"taskid":self.taskid,"title":self.title,"percent":self.percent,"status":self.status,"create_time":self.crate_time},cls=MyEncoder)
if __name__=="__main__":
    manager.run()
