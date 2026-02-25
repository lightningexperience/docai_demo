<h1> App Structure</h1>
I created this readme to explain how the repo contents are wired toegther. It's probably already obvious for expert Python developers, but for those new to Python, the following may help in easier navigation.

This is an explanation of how app.py and index.html are wired together.

Here is exactly how the HTML knows where to shoot that data, and how Python knows to catch it.
1. The HTML "Invisible" Rule
Normally, when you build an HTML form, you have to explicitly tell it where to send the data using an attribute called action. It looks like this:
<form action="https://my-heroku-app.com/process-data" method="POST">
But if you look at our index.html code, I left the action attribute out completely:
<form method="POST" enctype="multipart/form-data">
Here is the secret web browser rule: If you do not give a form an action URL, the browser automatically says, "Okay, I will just send this data right back to the exact same URL that I am currently sitting on."
So, if you are looking at your app at https://my-cool-ai-app.herokuapp.com/, clicking submit simply fires the data right back to https://my-cool-ai-app.herokuapp.com/.
2. How Python "Claims" that URL
Now that the browser fired the data back to your Heroku URL, how does app.py intercept it?
That is what this tiny, magical line of code does in app.py:
Python
@app.route("/", methods=["GET", "POST"])
def index():
That @app.route("/") is essentially a traffic cop.
•	The "/" means the "root" or homepage of your website (e.g., https://my-cool-ai-app.herokuapp.com/).
•	It tells your Heroku server: "If anyone visits this URL (GET), or sends data to this URL (POST), trigger the index() Python function immediately."
Putting it together: The Loop
1.	You visit your-app.com/.
2.	Python sees you visiting / and sends you the index.html file so you can see the webpage.
3.	You upload a file and click submit.
4.	Because the HTML form has no action, your browser fires the file right back to your-app.com/.
5.	Python is still standing guard at @app.route("/"). It sees the incoming file, grabs it, extracts the names, and sends a fresh copy of the HTML back to you with the new data plugged in.


You never directly visit index.html. Instead, you knock on app.py's door, and app.py hands you index.html to look at.
Here is exactly how that invisible hand-off happens when you type your URL into the browser and hit Enter.
1. You type the URL (The "GET" Request)
When you simply visit a website like https://your-app.herokuapp.com/, your web browser sends a message to the server saying, "Hey, I am here to GET whatever is on the homepage."
2. app.py Answers the Door
Remember that @app.route("/") line in your Python code? That means app.py is standing at the front door waiting for visitors.
When your browser's "GET" request arrives, app.py triggers the index() function:
Python
@app.route("/", methods=["GET", "POST"])
def index():
    extracted_data = None
    error_message = None

    # Python asks: Did they submit a file? (POST)
    if request.method == "POST":
        # ... (This gets SKIPPED because you are just visiting, which is a GET)
3. Python Skips the Math and Hands You the HTML
Because you are just visiting for the first time, your browser sent a GET request, not a POST request.
Python sees this, completely skips the entire if request.method == "POST": block (where the AI extraction happens), and drops straight down to the very last line of the function:
Python
    return render_template("index.html", data=extracted_data, error=error_message)
This single line is the magic trick. It tells Python: "The user just wants to see the page. Go into the templates folder, pick up the index.html file, and send it to their browser."
The Summary
1.	You visit the URL.
2.	app.py intercepts your visit.
3.	app.py realizes you haven't uploaded anything yet.
4.	app.py pushes index.html to your screen so you have a form to look at.
It acts as the middleman for everything. You never touch the HTML directly; app.py always serves it to you!

