# main.py

# Import packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'futura'
from bs4 import BeautifulSoup
import requests
from datetime import date, datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from scipy.ndimage import gaussian_filter1d


names = ['Alexis', 'Martin', 'Thomas']

def createScoresDf() :

    # Read in the predictions
    pred = pd.read_csv('Predictions.csv')
    # Scrape the actual standings
    url = 'https://fbref.com/en/comps/9/Premier-League-Stats'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'lxml')
    table = soup.find('table')
    pd.read_html(str(table))[0].MP.sum()
    standings = pd.read_html(str(table))[0]
    prog = round(100 * standings['MP'].sum() / (20 * 38), 1)
    standings = standings[['Squad']].rename(columns = {'Squad': 'Team'})
    # Merge standings and predictions
    data = pd.concat([standings, pred], axis = 1)
    # Compute by how much each players are off and score
    for name in names :
        data[f'Off{name}'] = [np.abs(np.where(data[name] == tm)[0][0] - idx) for tm, idx in zip(data.Team, data.index)]
        data[f'Perfect{name}'] = (data[name] == data['Team']).astype(int)

    data.to_csv(f'results/results-{str(date.today())}.csv')

    return prog


def getScorePerfects(name, filename) :

    data = pd.read_csv(filename)
    perfect = data[f'Perfect{name}'].sum()
    score = (200 - data[f'Off{name}'].sum()) / 2 + perfect

    return score, perfect

def plot(scores, files, sorted_names) :
    
    time = [datetime.strptime(file[8:18], '%Y-%m-%d') for file in files]

    _, ax = plt.subplots(figsize = (18, 9), facecolor = 'black')

    plt.gca().set_facecolor('black')
    plt.plot(time, gaussian_filter1d(scores[:,0], 0.4), c = 'green', marker = 'o', linewidth = 5, markersize = 10, label = 'Alexis', zorder = 3 - np.where(np.array(sorted_names) == 'Alexis')[0][0])
    plt.plot(time, gaussian_filter1d(scores[:,1], 0.4), c = 'red',   marker = 'o', linewidth = 5, markersize = 10, label = 'Martin', zorder = 3 - np.where(np.array(sorted_names) == 'Martin')[0][0])
    plt.plot(time, gaussian_filter1d(scores[:,2], 0.4), c = 'blue',  marker = 'o', linewidth = 5, markersize = 10, label = 'Thomas', zorder = 3 - np.where(np.array(sorted_names) == 'Thomas')[0][0])
    plt.plot(time, scores[:,0], c = 'green', linewidth = 1, alpha = 0.5, zorder = - np.where(np.array(sorted_names) == 'Alexis')[0][0])
    plt.plot(time, scores[:,1], c = 'red',   linewidth = 1, alpha = 0.5, zorder = - np.where(np.array(sorted_names) == 'Martin')[0][0])
    plt.plot(time, scores[:,2], c = 'blue',  linewidth = 1, alpha = 0.5, zorder = - np.where(np.array(sorted_names) == 'Thomas')[0][0])

    plt.xticks(time, pd.Series(time).apply(lambda x: datetime.strftime(x, '%d %b')), color = 'white')
    plt.yticks(np.arange(0, 120, 20), np.arange(0, 120, 20), color = 'white')
    plt.ylabel('Score', size = 32, color = 'white')
    plt.title('2023-24 PREMIER LEAGUE PREDICTIONS: scores over time', size = 36, color = 'white')

    ax.tick_params(axis = 'both', labelsize = 24)
    plt.grid(axis = 'y', color = 'white', linestyle = ':', alpha = 0.8)
    plt.ylim([0, 120])

    ax.spines['left'].set_color('white'); ax.spines['right'].set_color('white')
    ax.spines['bottom'].set_color('white'); ax.spines['top'].set_color('white') 

    lgd = plt.legend(edgecolor = 'white', labelcolor = 'white', fontsize = 24, loc = 'lower right')
    lgd.get_frame().set_facecolor('black')

    path = f'plots/plot-{str(date.today())}.jpg'
    plt.savefig(path, dpi = 400)
    plt.close()

    return path

def emailResults(scores, path, prog, sorted_names, sorted_scores) :

    # Create a MIMEMultipart object
    msg = MIMEMultipart()

    # Set the sender and recipient addresses
    l = scores[-1,:]
    leaders = list(np.array(names)[(np.argwhere(l == np.max(l)).flatten())])
    mult = len(leaders) > 1
    subject = 'PREMIER LEAGUE PREDICTIONS UPDATE: ' + f'{" & ".join(leaders)} {mult*"are"}{(1 - mult) * "is"} leading the way with {np.max(l)} points !'
    msg['Subject'] = subject

    my_mail = 'martinbog19@gmail.com'
    recipients = [my_mail, 'tbogaert19@gmail.com', 'alexis.bogaert2309@gmail.com']

    # Create the email body as HTML
    html = f"""
    <html>
    <body>
    <p>Rhoya la mif,</p>
    <p>Leaderboard after completion of {prog}% of the 2023-24 Premier League season:</p>
    <p style="margin-left: 20px;">1. {sorted_names[0]}:  {sorted_scores[0]} pts<br>
    <p style="margin-left: 20px;">2. {sorted_names[1]}:  {sorted_scores[1]} pts<br>
    <p style="margin-left: 20px;">3. {sorted_names[2]}:  {sorted_scores[2]} pts</p>
    <p><img src="cid:image1" alt="Image"></p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    # Read and attach the image
    with open(path, 'rb') as img_file:
        img = MIMEImage(img_file.read())
        img.add_header('Content-ID', '<image1>')
        msg.attach(img)

    with open('key.txt', 'r') as k :
        password = k.read()

    # Set up the SMTP server and send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(my_mail, password)
        server.sendmail(my_mail, recipients, msg.as_string())
        print('Email sent successfully!')
    except Exception as e:
        print('Error sending email: ', str(e))
    finally:
        server.quit()



def main() :

    prog = createScoresDf()
    
    files = sorted(os.listdir('results/'))
    scores, perfects = np.zeros((len(files), 3)), np.zeros((len(files), 3))

    for i, file in enumerate(files) :
        for j, name in enumerate(names) :

            score, perfect = getScorePerfects(name, 'results/' + file)
            scores[i,j]   = score
            perfects[i,j] = perfect
    
    current_scores = list(scores[-1,:])
    combined = list(zip(names, current_scores))
    sorted_combined = sorted(combined, key = lambda x: x[1], reverse = True)
    sorted_names, sorted_scores = zip(*sorted_combined)

    path = plot(scores, files, sorted_names)
    emailResults(scores, path, prog, sorted_names, sorted_scores)


if __name__ == '__main__' :

    main()