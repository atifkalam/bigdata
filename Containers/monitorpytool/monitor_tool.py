import base64
import io
import matplotlib.pyplot as plt
import pymongo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, render_template, session, g

app = Flask(__name__)
app.secret_key = 'your_secret_key'

scheduler = BackgroundScheduler()


def get_db():
    if 'db' not in g:
        g.db = pymongo.MongoClient("mongodb://dbstorage:27017")["cloneDetector"]
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.client.close()


def get_data():
    db = get_db()
    files = db["files"]
    clones = db["clones"]
    candidates = db["candidates"]
    chunks = db["chunks"]
    file_count = files.count_documents({})
    clone_count = clones.count_documents({})
    chunk_count = chunks.count_documents({})
    candidate_count = candidates.count_documents({})

    data = [
        {
            'files': file_count,
            'clones': clone_count,
            'chunks': chunk_count,
            'candidates': candidate_count,
        }]
    return data


def my_cron_job():
    db = get_db()
    global data
    global chunk_data, clone_data, file_data, candidate_data

    data = get_data()
    chunk_diff = abs(session['chunk_tot'] - data[0]['chunks'])
    clone_diff = abs(session['clone_tot'] - data[0]['clones'])
    file_diff = abs(session['file_tot'] - data[0]['files'])

    if chunk_diff != 0: chunk_data.append(chunk_diff)
    if clone_diff != 0: clone_data.append(clone_diff)
    if file_diff != 0: file_data.append(file_diff)

    session['chunk_tot'] = data[0]['chunks']
    session['clone_tot'] = data[0]['clones']
    session['file_tot'] = data[0]['files']


def build_plot():
    img = io.BytesIO()

    y_chunk = chunk_data
    x_chunk = range(len(chunk_data))

    y_clone = clone_data
    x_clone = range(len(clone_data))

    y_file = file_data
    x_file = range(len(file_data))

    y_candidate = candidate_data
    x_candidate = range(len(candidate_data))

    fig, axs = plt.subplots(2, 2)
    axs[0, 0].plot(x_chunk, y_chunk)
    axs[0, 0].set_title('Chunks/min')
    axs[0, 1].plot(x_clone, y_clone, 'tab:orange')
    axs[0, 1].set_title('Clones/min')
    axs[1, 0].plot(x_file, y_file, 'tab:green')
    axs[1, 0].set_title('Files/min')
    axs[1, 1].plot(x_candidate, y_candidate, 'tab:red')
    axs[1, 1].set_title('Candidates')

    for ax in axs.flat:
        ax.set(xlabel='min', ylabel='items processed')

    for ax in axs.flat:
        ax.label_outer()

    plt.savefig(img, format='png')
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return '<img src="data:image/png;base64,{}">'.format(plot_url)


# Initialize lists
chunk_data = []
clone_data = []
file_data = []
candidate_data = []


@app.before_request
def before_request():
    session.setdefault('chunk_tot', 0)
    session.setdefault('clone_tot', 0)
    session.setdefault('file_tot', 0)


@app.route('/')
def stats():
    global data

    # Call the functions to update data, chunk_data, clone_data, and file_data
    my_cron_job()

    plot = build_plot()
    data = get_data()
    return render_template('index.html', data=data, plot=plot)


if __name__ == "__main__":
    # Schedule the cron job to run every minute
    scheduler.add_job(
        func=my_cron_job,
        trigger=CronTrigger.from_crontab('* * * * *'),
    )
    scheduler.start()

    app.run(debug=True)
