from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html') ##'Hello, World! This Profile About Route'

@app.route('/contact')
def hello_c():
    return 'Hello, This Contact Person Instagram @fuaddddddd'

@app.route('/profile')
def hello_p():
    return 'Hello, This is Profile Fuad Atoil'

if __name__ == '__main__':
    app.run(debug=True)