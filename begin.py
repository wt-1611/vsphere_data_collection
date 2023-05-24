from flask import Flask, render_template,request,redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import vsphere,os
from werkzeug.security import generate_password_hash,check_password_hash#转换密码用到的库

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my.sqlite'

db = SQLAlchemy(app)

class vs(db.Model):
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(45))
    addr = db.Column(db.String(45), unique=True,nullable=False)
    password = db.Column(db.String(128))
    port = db.Column(db.Integer)
    description = db.Column(db.String(256),default="nothing")




    def __init__(self,username,addr,password,description,port):
        self.addr = addr
        self.username = username
        self.password = password
        self.description = description
        self.port = port




with app.app_context():
   db.create_all()

@app.route("/test")
def test():
   return  render_template("info.html")


@app.route("/details")
def details():
    foo = vs.query.filter_by(addr=request.args['addr']).first()

    all = vsphere.main(ip=foo.addr,user=foo.username,port=foo.port,pwd=foo.password)

    if all[0]:
        hardwordINFO = all[0]
        hostRUN = all[1]
        vDataStore = all[2]
        vm = all[3]
        return render_template("info.html",
                               hardwordINFO=hardwordINFO,
                               harwordkey=hardwordINFO[0].keys(),
                               hostrunkey=hostRUN[0].keys(),
                               hostRUN=hostRUN,
                               DataStorekey=vDataStore[0].keys(),
                               DataStore=vDataStore,
                               vm=vm,
                               vmkey=vm[0].keys(),
                               ip=foo.addr)
    else:
        print(all)
        return render_template("table.html",vs=vs.query.all(),flag=all)


@app.route("/delete")
def delete():
    addr = request.args.get('addr')
    d = vs.query.filter_by(addr=addr).first()
    db.session.delete(d)
    db.session.commit()
    return redirect(url_for('select'))



@app.route("/")
def select():
    cc=(1,2,3)
    return render_template("table.html",vs=vs.query.all(),flag=cc)


@app.route("/add")
def add():
    return render_template("iframe.html")

@app.route("/input",methods = ['POST'])
def input():
    if request.method == "POST":
        try:
            ip = request.form['ip']
            passwd = request.form['pass']
            username = request.form['username']
            description = request.form['des']
            port = request.form['port']
            check = vs.query.filter_by(addr=ip).all()

            if ip:
                if check:
                    message = f"地址 {ip},已经存在!"
                    flag = 0
                else:
                    p = vs(username=username,addr=ip,password=passwd,description=description,port=port)
                    db.session.add(p)
                    db.session.commit()
                    message = "提交成功"
                    flag = 1
            else:
                message = "请输入vCenter地址！！"
                flag = 0

        except:
            message = f"未知错误，请联系开发者!!"
            flag = 0

    return render_template('iframe.html',ms=message,flag=flag)


if __name__ == '__main__':
   app.run(debug = True,host="0.0.0.0")
