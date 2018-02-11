#!/usr/bin/env python2.7


import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Markup,flash, Flask, abort,session,request, render_template, g, redirect, Response
import time as t
import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key='123456'


DATABASEURI = "postgresql://cz2498:123456@35.196.90.148/proj1part2"

engine = create_engine(DATABASEURI)



@app.before_request
def before_request():
  
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():

  print request.args
  
  return render_template("index.html")


@app.route('/restaurants')
def restaurants():
	entries = g.conn.execute('select * from restaurants')
	entries2 = g.conn.execute('select * from restaurants')
    # entries = [dict(name_rest=row[1], name_addr=row[3]) for row in cur.fetchall()]
	return render_template('restaurants.html', entries=entries,entries2=entries2)

@app.route('/food')
def food():
	entries=g.conn.execute('select * from food');
	entries2=g.conn.execute('select * from food');
	return render_template('food.html', entries=entries,entries2=entries2)
	
	
@app.route('/ingredients/',methods=['GET','POST'])
def ingredients():
	if request.method == 'POST':
		name_food=request.form['name_food']	
	entries=[]
	data=[]
	try:
		print name_food
		entries = g.conn.execute('select * from ingredients i, consists_of c where i.name_ingredient=c.name_ingredient and c.name_food=(%s)',[name_food])
		data=entries.fetchall()
	except Exception as e:
		error = e
		flash('no this food')
		return render_template('/')
	else :
		return render_template('ingredients.html', entries=data)
		
@app.route('/food2/',methods=['GET','POST'])
def food2():
	if request.method == 'POST':
		id_rest=request.form['id_rest']	
	entries=[]
	data=[]
	try:
		entries = g.conn.execute('select * from cooks c , food f where c.id_rest=(%s) and f.name_food=c.name_food',[id_rest]).fetchall()
		entries2 = g.conn.execute('select * from food f, cooks c where c.id_rest=(%s) and f.name_food=c.name_food',[id_rest]).fetchall()
	except Exception as e:
		error = e
		flash('no this food')
		return render_template('/')
	else :
		return render_template('food2.html', entries=entries,entries2=entries2)
@app.route('/consists_of')
def consists_of():
  entries = g.conn.execute('select c.name_ingredient,c.name_food,i.type from consists_of c, ingredients i  where i.name_ingredient=c.name_ingredient').fetchall()
  return render_template('consists_of.html', entries=entries)	

@app.route('/register/', methods=['GET','POST'])
def register():
	
	db = g.conn
	error = None	
	time=[]
	name_user=[]
	password=[]
	phone=[]
	email=[]
	type=[]
	id_user=int(t.time())
	if request.method == 'POST':
		name_user = request.form['username']
		password = request.form['password']
		phone=request.form['phone']
		email=request.form['email']
		type_user=request.form['type']
		name_addr=request.form['address']
		zip=request.form['zip']
		if (len(name_user)>19):
			flash('too long for name')
			return redirect('/')
		if (len(password)>19):
			flash('too long for password')
			return redirect('/')
		if (len(email)>49):
			flash('too long for email')
			return redirect('/')
		# if (phone>999999999):
			# flash('not a phone')
			# return redirect('/')
		try:
			usercheck=db.execute('select * from users where name_user=(%s) and password=(%s)',name_user,password).fetchall()
			if (len(usercheck)>0):
				flash ('plz change name or password')
				return redirect('/')
			emailcheck=db.execute('select * from users where email=(%s)',email).fetchall()
			if (len(emailcheck)>0):
				flash ('plz change email')
				return redirect('/')
			phonecheck=db.execute('select * from users where phone=(%s)',phone).fetchall()
			if (len(phonecheck)>0):
				flash ('plz change phone')
				return redirect('/')
			db.execute('insert into users VALUES((%s),(%s),(%s),(%s),(%s),(%s))', [id_user, type_user,password,name_user,phone, email])
			db.execute('insert into addresses VALUES ((%s),(%s))',[name_addr,zip])
			db.execute('insert into locate_in VALUES ((%s),(%s))',[id_user,name_addr])
			flash('Register success')		
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/')
	

	
@app.route('/order/<id>/addorder/', methods=['GET','POST'])
def order_add(id=None):
	id=session.get('id')
	if not id:
		abort(401)
		
	db = g.conn
	error = None	
	time=[]
	name_food=[]
	name_rest=[]
	id_order=int(t.time())
	if request.method == 'POST':
		name_food = request.form['food']
		id_rest = request.form['restaurant']    		
		try:
			date=datetime.datetime.now().date().isoformat()
			cursor=db.execute('select c.price,r.id_rest from cooks c, restaurants r where c.id_rest=r.id_rest and c.name_food=(%s) and r.id_rest=(%s)',name_food,id_rest).fetchall()
			if (len(cursor)>0):
				for row in cursor:
					price=row['price']
					# id_rest=row['id_rest']
				db.execute('insert into orderlists VALUES((%s),(%s),(%s),(%s))', [id_order, price, date,id])
				db.execute('insert into makes VALUES ((%s),(%s),(%s))',[name_food,id_rest,id_order])
				flash('order success')
			else:
				flash('no item!')
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/') 
	
@app.route('/order/<id>/updateorder/', methods=['GET','POST'])
def order_update(id=None):
	id=session.get('id')
	if not id:
		abort(401)
		
	db = g.conn
	error = None	
	time=[]
	name_food=[]
	name_rest=[]
	id_order=[]
	oldprice=0
	price=0
	if request.method == 'POST':
		name_food = request.form['food']
		name_rest = request.form['restaurant']    
		id_order=request.form['orderid'] 		
		try:
			date=datetime.datetime.now().date().isoformat()
			cursor=db.execute('select c.price,r.id_rest from cooks c, restaurants r where c.id_rest=r.id_rest and c.name_food=(%s) and r.name_rest=(%s)',name_food,name_rest).fetchall() ####query the food
			ordercheck=db.execute('select o.id_order,r.name_rest,m.name_food,o.cost,o.time from orderlists o, makes m,restaurants r where o.id_order=m.id_order and m.id_rest=r.id_rest and o.id_user=(%s) and o.id_order=(%s) and m.name_food=(%s) and r.name_rest=(%s)' , id,id_order,name_food,name_rest).fetchall() ### query 
			existcheck=db.execute('select o.id_order, o.cost from orderlists o where o.id_user=(%s) and o.id_order=(%s) ' , id,id_order).fetchall()
			if (len(ordercheck)>0):
				flash('can not add same item in same order!')
				return redirect('/') 
			if (len(existcheck)==0):
				flash('no this order, do you want a new order?')
				return redirect('/')
			else:
				for row in existcheck:
					oldprice=row['cost']
			if (len(cursor)>0):
				for row in cursor:
					price=row['price']+oldprice
					id_rest=row['id_rest']
				# db.execute('insert into orderlists VALUES((%s),(%s),(%s),(%s))', [id_order, price, date,id])
				db.execute('insert into makes VALUES ((%s),(%s),(%s))',[name_food,id_rest,id_order])
				db.execute('update orderlists set cost=(%s) where id_order=(%s)',price,id_order)
				flash('order success')
			else:
				flash('no item!')
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/') 

@app.route('/order/<id>/')
def order(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	orderlist=[]
	db = g.conn
	error = None
	try:
		orderlist = db.execute('select o.id_order,r.name_rest,m.name_food,o.cost,o.time from orderlists o, makes m,restaurants r, users u where u.id_user=o.id_user and o.id_order=m.id_order and m.id_rest=r.id_rest and u.id_user=(%s) order by o.id_order ASC' , id).fetchall()
		orderlist2 = db.execute('select o.id_order,r.name_rest,m.name_food,o.cost,o.time from orderlists o, makes m,restaurants r, users u where u.id_user=o.id_user and o.id_order=m.id_order and m.id_rest=r.id_rest and u.id_user=(%s) order by o.id_order ASC' , id).fetchall()
		rest=db.execute('select r.name_rest,r.id_rest from restaurants r').fetchall()
		# for row in profile:
			# name=row['name_user']
			# phone=row['phone']
			# email=row['email']
		# for row in locates:
			# address=row['name_addr']
	except AttributeError:
		error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
	except Exception as e:
		error = e
	# return render_template('profile.html', name=name,phone=phone,email=email,address=address,error=error)
	return render_template('order.html', orderlist=orderlist,error=error,orderlist2=orderlist2,rest=rest)
  	
	
@app.route('/profile/<id>/update/', methods=['GET','POST'])
def user_update(id=None):
	id=session.get('id')
	if not id:
		abort(401)

	db = g.conn
	error = None
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']    
		phone = request.form['phone']
		if (len(name)>19):
			flash('too long for name')
			return redirect('/')
		# if (phone>999999999):
			# flash('not a phone')
			# return redirect('/')
		password=[]
		try:
			existcheck=db.execute('select * from users where id_user=(%s)',id).fetchall()
			for row in existcheck:
				password=row['password']
			usercheck=db.execute('select * from users where name_user=(%s) and password=(%s)',name,password).fetchall()
			if (len(usercheck)>0):
				flash ('plz change name or password')
				return redirect('/')
			emailcheck=db.execute('select * from users where email=(%s)',email).fetchall()
			if (len(emailcheck)>0):
				flash ('plz change email')
				return redirect('/')
			phonecheck=db.execute('select * from users where phone=(%s)',phone).fetchall()
			if (len(phonecheck)>0):
				flash ('plz change phone')
				return redirect('/')
			db.execute('update users set name_user=(%s), email=(%s), phone=(%s) where id_user=(%s)', [name, email, phone,id])
			session['name'] = name
			flash('Update Profile Success!')
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/')  
	
@app.route('/profile/<id>/')
def user(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	name=[]
	phone=[]
	email=[]
	address=[]
	profile=[]
	locates=[]
	db = g.conn
	error = None
	try:
		profile = db.execute('select * from users where id_user=(%s)', id).fetchone()
		locates=db.execute('select l.name_addr,a.zip from users u, locate_in l, addresses a where u.id_user=(%s) and l.id_user=u.id_user and a.name_addr=l.name_addr',id).fetchall()
		# for row in profile:
			# name=row['name_user']
			# phone=row['phone']
			# email=row['email']
		# for row in locates:
			# address=row['name_addr']
	except AttributeError:
		error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
	except Exception as e:
		error = e
	# return render_template('profile.html', name=name,phone=phone,email=email,address=address,error=error)
	return render_template('profile.html', profile=profile,locates=locates,error=error)

@app.route('/profile/<id>/addr_update/', methods=['GET','POST'])
def addr_update(id=None):
	id=session.get('id')
	if not id:
		abort(401)

	db = g.conn
	error = None
	if request.method == 'POST':
		oldaddr= request.form['oldaddress']
		newaddr= request.form['newaddress']
		if (len(newaddr)>49):
			flash('too long for address')
			return redirect('/')
		newzip=request.form['newzip']
		try:
			check=db.execute('select * from addresses where name_addr=(%s)',newaddr).fetchall()
			if (len(check)>0):
				db.execute('update locate_in set name_addr=(%s), id_user=(%s) where name_addr=(%s) and id_user=(%s)',newaddr,id,oldaddr,id)
			else:
				db.execute('update addresses set name_addr=(%s), zip=(%s) where name_addr=(%s)', [newaddr, newzip, oldaddr])
			flash('Update Addr Success!')
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/') 
	
@app.route('/profile/<id>/addr_add/', methods=['GET','POST'])
def addr_add(id=None):
	id=session.get('id')
	if not id:
		abort(401)

	db = g.conn
	error = None
	if request.method == 'POST':
		newaddr= request.form['newaddress']
		newzip=request.form['newzip']
		if (len(newaddr)>49):
			flash('too long for address')
			return redirect('/')
		check=db.execute('select * from addresses where name_addr=(%s)',newaddr).fetchall()
		if (len(check)==0):
			try:
				db.execute('insert into addresses VALUES((%s),(%s))', [newaddr, newzip])
				db.execute('insert into locate_in VALUES((%s),(%s))', [id,newaddr])
				flash('Add Address Success!')
			except AttributeError:
				error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
				flash(error)
			except Exception as e:
				error = e
				flash(error)
			return redirect('/') 
		else:
			check_locate=db.execute('select * from locate_in where name_addr=(%s) and id_user=(%s)',newaddr,id).fetchall()
			if (len(check_locate)==0):
				try:
					db.execute('insert into locate_in VALUES((%s),(%s))', [id,newaddr])
					flash('Add Address Success!')
				except AttributeError:
					error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
					flash(error)
				except Exception as e:
					error = e
					flash(error)
				return redirect('/') 
			else:
				flash('exist')
				return redirect('/') 
@app.route('/profile/<id>/addr_delete/', methods=['GET','POST'])
def addr_delete(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	db = g.conn
	error = None	
	id_rest=[]
	name_food=[]
	price=[]
	if request.method == 'POST':
		name_addr=request.form['oldaddress']	
		try:
			count=db.execute('delete from locate_in where id_user=(%s) and name_addr=(%s)',[id,name_addr])	
			flash('Delete Address Success!')	
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/')
	
	
	
@app.route('/manage/<id>/')
def manage(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	
	profile = []
	profile2=[]
	order=[]
	food=[]
	db = g.conn
	error = None
	try:
		profile = db.execute('select * from restaurants where id_user=(%s) order by restaurants.id_rest', id).fetchall()
		profile2 = db.execute('select * from restaurants where id_user=(%s) order by restaurants.id_rest', id).fetchall()
		order=db.execute(' select u.name_user, u.phone, o.id_order,o.time,r.name_rest ,m.name_food from orderlists o, users u, restaurants r, makes m where u.id_user=o.id_user and r.id_rest=m.id_rest and o.id_order=m.id_order and r.id_user=(%s) order by o.id_order',id).fetchall()
		food=db.execute('select c.name_food,r.name_rest from cooks c, restaurants r where c.id_rest=r.id_rest and r.id_user=(%s)',id).fetchall()
	except AttributeError:
		error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
	except Exception as e:
		error = e
	return render_template('manage.html', profile=profile ,order=order,food=food,error=error,profile2=profile2)	
	
@app.route('/manage/update_rest/', methods=['GET','POST'])
def rest_update(id=None):
	id=session.get('id')
	if not id:
		abort(401)

	db = g.conn
	error = None
	oldname=[]
	if request.method == 'POST':
		
		newname = request.form['to']  
		id_rest = request.form['id'] 	
		if id_rest==[]:
			flash('Do not kidding!You do not have a restaurant')
			return redirect('/')
			
		try:
			check=db.execute('select * from restaurants r where r.id_user=(%s) and r.id_rest=(%s)',id,id_rest).fetchall()
			if (len(check)==0):
				flash('no this restaurant!')
				return redirect('/')
			else:
				for row in check:
					oldname=row['name_rest']
			db.execute('update restaurants set name_rest=(%s) where id_user=(%s) and id_rest= (%s)and name_rest=(%s)', [newname,id,id_rest,oldname])
			flash('Update Restaurant Success!')
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/')  
	
@app.route('/manage/<id>/rest_create/', methods=['GET','POST'])
def rest_create(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	db = g.conn
	error = None	
	time=[]
	name_rest=[]
	password=[]
	phone=[]
	email=[]
	type=[]
	id_rest=int(t.time())
	date=datetime.datetime.now().date().isoformat()
	if request.method == 'POST':
		name_rest = request.form['name_rest']
		name_addr=request.form['address']
		zip=request.form['zip']
		if (len(name_rest)>19):
			flash('too long for name')
			return redirect('/')
		if (len(name_addr)>49):
			flash('too long for address')
			return redirect('/')
		check=db.execute('select * from addresses where name_addr=(%s)',name_addr).fetchall()
		try:
			if (len(check)==0):
				db.execute('insert into addresses VALUES ((%s),(%s))',[name_addr,zip])
			db.execute('insert into restaurants VALUES((%s),(%s),(%s),(%s),(%s))', [id_rest, name_rest,id,name_addr,date])
			flash('Register success')		
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/') 

@app.route('/manage/<id>/rest_delete/', methods=['GET','POST'])
def rest_delete(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	db = g.conn
	error = None	
	id_rest=[]
	if request.method == 'POST':
		id_rest = int(request.form['id'])
		
		try:
			check=db.execute('select * from restaurants r where r.id_user=(%s) and r.id_rest=(%s)',id,id_rest).fetchall()
			if (len(check)==0):
				flash('no this restaurant!')
				return redirect('/')
			db.execute('delete from restaurants where id_rest=(%s)',[id_rest])
			db.execute('delete from cooks where id_rest=(%s)',[id_rest])			
			flash('Delete success')		
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/') 	
	
@app.route('/manage/<id>/food_add/', methods=['GET','POST'])
def food_add(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	db = g.conn
	error = None	
	id_rest=[]
	name_food=[]
	price=[]
	if request.method == 'POST':
		id_rest = int(request.form['id_rest'])
		name_food=request.form['name_food']	
		price=request.form['price']
		if (len(name_food)>49):
			flash('too long for food')
			return redirect('/')
		try:
			check=db.execute('select * from food where food.name_food=(%s)',name_food).fetchall()
			if (len(check)==0):
				db.execute('insert into food (name_food) VALUES ((%s))',[name_food])
			checkrest=db.execute('select * from restaurants where id_rest=(%s) and id_user=(%s)',id_rest,id).fetchall()
			if (len(checkrest)==0):
				flash('no this restaurant')
				return redirect('/')
			checkexist=db.execute('select * from cooks c where c.name_food=(%s) and c.id_rest=(%s)',name_food,id_rest).fetchall()
			if (len(checkexist)>0):
				flash('there already this food, do you want to add new one?')
				return redirect('/')
			db.execute('insert into cooks VALUES ((%s),(%s),(%s))',[price,name_food,id_rest])			
			flash('Register food success')		
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/')
	
@app.route('/manage/<id>/food_delete/', methods=['GET','POST'])
def food_delete(id=None):
	id=session.get('id')
	if not id:
		abort(401)
	db = g.conn
	error = None	
	id_rest=[]
	if request.method == 'POST':
		id_rest = request.form['id_rest']
		name_food=request.form['name_food']
		try:
			check=db.execute('select * from cooks where id_rest=(%s) and name_food=(%s)',[id_rest,name_food]).fetchall()
			if (len(check)==0):
				flash ('no this food in this restaurant')
				return redirect('/')
			db.execute('delete from cooks where id_rest=(%s) and name_food=(%s)',[id_rest,name_food])
						
			flash('Delete success')		
		except AttributeError:
			error = 'FATAL:  remaining connection slots are reserved for non-replication superuser connections'
			flash(error)
		except Exception as e:
			error = e
			flash(error)
	return redirect('/') 	


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
		name = request.form['username']
		password=request.form['password']
		cursor = g.conn.execute('SELECT * from users where name_user = (%s) and password=(%s)', name,password)
		data=cursor.fetchall()
		if len(data)==0:
			error = 'Invalid username or password'
		else:
			session['logged_in'] = True
			session['name']=name
			for row in data:
				session['id']=row['id_user']
				session['type']=row['type_user']
			flash('You were logged in!')
			return render_template('index.html', error=error)
    return render_template('index.html', error=error)


	
@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    session.pop('id',None)
    session.pop('type',None)	
    session.pop('name', None)
    flash('You were logged out')
    return redirect('/')


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=True, threaded=threaded)


  run()
