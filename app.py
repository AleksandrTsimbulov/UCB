from flask import render_template
import connexion

app = connexion.App(__name__, specification_dir='openapi/')
app.add_api('swagger.yaml')


@app.route('/')
def todo():
    return render_template('welcome.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000, debug=True)
