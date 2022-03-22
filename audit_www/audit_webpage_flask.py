from flask import Flask, render_template, url_for

app = Flask(__name__)

posts = [
	{
		'author' : 'Anil Singh',
		'title' : 'Audit Framework',
		'content' : 'Audit Framework 1.0',
		'ts' : 'Feb 19, 2021'
	},
	{
		'author' : 'Anil Singh',
		'title' : 'CICD',
		'content' : 'CICD Pipelines 1.0',
		'ts' : 'Feb 21, 2021'
	}
]

@app.route("/")
@app.route("/home")
def home():
	return render_template('home.html', posts=posts)

@app.route("/about")
def about():
	return render_template('about.html',title = 'About')
	
if __name__ == "__main__":
	app.run(debug=True)