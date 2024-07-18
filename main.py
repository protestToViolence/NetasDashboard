from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///politicians.db'
db = SQLAlchemy(app)

class Politician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    promises_made = db.Column(db.Integer, default=0)
    promises_fulfilled = db.Column(db.Integer, default=0)
    promises_in_progress = db.Column(db.Integer, default=0)
    promises_dont_care = db.Column(db.Integer, default=0)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    success_rate = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/admin')
def admin_dashboard():
    politicians = Politician.query.all()
    projects = Project.query.all()
    return render_template('admin_dashboard.html', politicians=politicians, projects=projects)

@app.route('/add_politician', methods=['GET', 'POST'])
def add_politician():
    if request.method == 'POST':
        new_politician = Politician(
            name=request.form['name'],
            party=request.form['party'],
            age=int(request.form['age']),
            promises_made=int(request.form['promises_made']),
            promises_fulfilled=int(request.form['promises_fulfilled']),
            promises_in_progress=int(request.form['promises_in_progress']),
            promises_dont_care=int(request.form['promises_dont_care'])
        )
        db.session.add(new_politician)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_politician.html')

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        new_project = Project(
            name=request.form['name'],
            status=request.form['status'],
            success_rate=float(request.form['success_rate'])
        )
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_project.html')

# Initialize the Dash app
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

# Layout
dash_app.layout = html.Div([
    html.H1("Indian Politicians Dashboard"),
    
    dcc.Dropdown(
        id='politician-dropdown',
        options=[],  # We'll populate this in a callback
        value=None
    ),
    
    html.Div([
        html.H2("Promises"),
        dcc.Graph(id='promises-graph')
    ]),
    
    html.Div([
        html.H2("Projects Status (1 year after completion)"),
        dcc.Graph(id='projects-graph')
    ]),
    
    html.Button('Print Dashboard', id='print-button'),
    html.Div(id='print-content', style={'display': 'none'})
])

@dash_app.callback(
    Output('politician-dropdown', 'options'),
    Output('politician-dropdown', 'value'),
    Input('politician-dropdown', 'search_value')
)
def update_dropdown(_):
    with app.app_context():
        politicians = Politician.query.all()
        options = [{'label': p.name, 'value': p.id} for p in politicians]
        value = options[0]['value'] if options else None
    return options, value

@dash_app.callback(
    Output('promises-graph', 'figure'),
    Input('politician-dropdown', 'value')
)
def update_promises_graph(selected_politician_id):
    with app.app_context():
        politician = Politician.query.get(selected_politician_id)
        if politician:
            df = pd.DataFrame({
                'Status': ['Fulfilled', 'In Progress', "Don't Care"],
                'Count': [politician.promises_fulfilled, politician.promises_in_progress, politician.promises_dont_care]
            })
            fig = px.pie(df, values='Count', names='Status', title=f"Promises by {politician.name}")
            return fig
    return {}

@dash_app.callback(
    Output('projects-graph', 'figure'),
    Input('politician-dropdown', 'value')
)
def update_projects_graph(_):
    with app.app_context():
        projects = Project.query.all()
        df = pd.DataFrame([(p.name, p.status, p.success_rate) for p in projects], 
                          columns=['Project', 'Status', 'Success Rate'])
        fig = px.bar(df, x='Project', y='Success Rate', color='Status', 
                     title="Project Success Rates (1 year after completion)")
        return fig

if __name__ == '__main__':
    app.run(debug=True)